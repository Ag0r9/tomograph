import math
import copy

import numpy as np
import skimage.io
import skimage.draw
import streamlit as st


def initial_kernel():
    kernel_half = np.array([-4 / np.pi ** 2 / i ** 2 for i in range(1, 11)])
    kernel = np.concatenate((np.zeros(1), kernel_half))
    kernel[::2] = 0
    kernel[0] = 1
    return kernel


def get_radius(picture):
    return math.ceil((picture.shape[0] ** 2 / 4 + picture.shape[1] ** 2 / 4) ** 0.5)


def pad_image(picture, radius):
    return np.pad(picture, ((radius - picture.shape[0] // 2, radius - picture.shape[0] // 2 + 1),
                            (radius - picture.shape[1] // 2, radius - picture.shape[1] // 2 + 1)))


def get_coords(radius, angle):
    return int(radius * (math.cos(angle) + 1)), int(radius * (math.sin(angle) + 1))


class Tomograph:
    def __init__(self, image, step=8, no_of_detectors=100, bandwidth=90):
        self.original_image = image
        self.step = step
        self.no_of_detectors = no_of_detectors
        self.bandwidth = bandwidth
        self.kernel = initial_kernel()
        self.sinogram = None
        self.filtered_sinogram = None
        self.image_result = None
        self.image_filtered_result = None
        self.image_storage = None
        self.image_filtered_storage = None

    def bresenham_algorithm(self, rotation, bandwidth_pi, radius, detector):
        emitter_angle = rotation - bandwidth_pi / 2 + detector * bandwidth_pi / (self.no_of_detectors - 1)
        detector_angle = rotation + np.pi + bandwidth_pi / 2 - detector * bandwidth_pi / (self.no_of_detectors - 1)
        emitter_x, emitter_y = get_coords(radius, emitter_angle)
        detector_x, detector_y = get_coords(radius, detector_angle)
        return skimage.draw.line_nd((emitter_y, emitter_x), (detector_y, detector_x), endpoint=True)

    def process(self):
        views = int(360 // self.step)
        self.n_views_stored = min(views, 10)
        step_pi = self.step / 180 * np.pi
        bandwidth_pi = self.bandwidth / 180 * np.pi

        radius = get_radius(self.original_image)

        self.original_image = pad_image(self.original_image, radius)

        self.sinogram = np.zeros((views, self.no_of_detectors), dtype=np.float64)
        self.filtered_sinogram = np.zeros((views, self.no_of_detectors), dtype=np.float64)
        self.image_result = np.zeros_like(self.original_image)
        self.image_filtered_result = np.zeros_like(self.original_image)
        self.image_storage = np.zeros((self.n_views_stored, *self.original_image.shape), dtype=np.float64)
        self.image_filtered_storage = np.zeros_like(self.image_storage)

        rotation = np.pi
        views_stored = 0
        for view in range(views):
            rotation += step_pi
            for detector in range(self.no_of_detectors):
                line = self.bresenham_algorithm(rotation, bandwidth_pi, radius, detector)
                self.sinogram[view, detector] = self.original_image[line].mean()
                self.image_result[line] += self.sinogram[view, detector]

            self.filtered_sinogram[view, :] = np.convolve(self.sinogram[view, :], self.kernel, mode="same")

            for detector in range(self.no_of_detectors):
                line = self.bresenham_algorithm(rotation, bandwidth_pi, radius, detector)
                self.image_filtered_result[line] += self.filtered_sinogram[view, detector]

            if view * (self.n_views_stored - 1) // (views - 1) >= views_stored:
                self.image_storage[views_stored, :, :] = copy.deepcopy(self.image_result)
                self.image_filtered_storage[views_stored, :, :] = copy.deepcopy(self.image_filtered_result)
                views_stored += 1
