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


def get_coords(radius, angle):
    return int(radius * (math.cos(angle) + 1)), int(radius * (math.sin(angle) + 1))


class Tomograph:
    def __init__(self, image, step=8, no_of_detectors=100, bandwidth=90):
        self.original_image = image
        self.no_of_detectors = no_of_detectors
        self.views = int(360 // step)
        self.n_views_stored = min(self.views, 10)
        self.step_pi = step / 180 * np.pi
        self.radius = get_radius(self.original_image)
        self.bandwidth_pi = bandwidth / 180 * np.pi
        self.kernel = initial_kernel()
        self.sinogram = np.zeros((self.views, self.no_of_detectors), dtype=np.float64)
        self.filtered_sinogram = np.zeros((self.views, self.no_of_detectors), dtype=np.float64)
        self.result = np.zeros_like(self.original_image)
        self.filtered_result = np.zeros_like(self.original_image)
        self.storage = np.zeros((self.n_views_stored, *self.original_image.shape), dtype=np.float64)
        self.filtered_storage = np.zeros_like(self.storage)

    @st.cache
    def get_filtered_sinogram(self):
        return self.filtered_sinogram

    @st.cache
    def get_sinogram(self):
        return self.sinogram

    @st.cache
    def get_filtered_result(self):
        return self.filtered_result

    @st.cache
    def get_result(self):
        return self.result

    @st.cache
    def get_filtered_storage(self):
        return self.filtered_storage

    @st.cache
    def get_storage(self):
        return self.storage

    def initial_arrays(self):
        self.sinogram = np.zeros((self.views, self.no_of_detectors), dtype=np.float64)
        self.filtered_sinogram = np.zeros((self.views, self.no_of_detectors), dtype=np.float64)
        self.result = np.zeros_like(self.original_image)
        self.filtered_result = np.zeros_like(self.original_image)
        self.storage = np.zeros((self.n_views_stored, *self.original_image.shape), dtype=np.float64)
        self.filtered_storage = np.zeros_like(self.storage)

    def bresenham_algorithm(self, rotation, detector):
        emitter_angle = rotation - self.bandwidth_pi / 2 + detector * self.bandwidth_pi / (self.no_of_detectors - 1)
        detector_angle = rotation + np.pi + self.bandwidth_pi / 2 - detector * self.bandwidth_pi / (
                    self.no_of_detectors - 1)
        emitter_x, emitter_y = get_coords(self.radius, emitter_angle)
        detector_x, detector_y = get_coords(self.radius, detector_angle)
        return skimage.draw.line_nd((emitter_y, emitter_x), (detector_y, detector_x), endpoint=True)

    def pad_image(self, picture):
        return np.pad(picture, ((self.radius - picture.shape[0] // 2, self.radius - picture.shape[0] // 2 + 1),
                                (self.radius - picture.shape[1] // 2, self.radius - picture.shape[1] // 2 + 1)))

    def radon(self):
        rotation = np.pi
        views_stored = 0
        for view in range(self.views):
            rotation += self.step_pi
            for detector in range(self.no_of_detectors):
                line = self.bresenham_algorithm(rotation, detector)
                self.sinogram[view, detector] = self.original_image[line].mean()
                self.result[line] += self.sinogram[view, detector]

            self.filtered_sinogram[view, :] = np.convolve(self.sinogram[view, :], self.kernel, mode="same")

            for detector in range(self.no_of_detectors):
                line = self.bresenham_algorithm(rotation, detector)
                self.filtered_result[line] += self.filtered_sinogram[view, detector]

            if view * (self.n_views_stored - 1) // (self.views - 1) >= views_stored:
                self.storage[views_stored, :, :] = copy.deepcopy(self.result)
                self.filtered_storage[views_stored, :, :] = copy.deepcopy(self.filtered_result)
                views_stored += 1

    def process(self):
        self.original_image = self.pad_image(self.original_image)
        self.initial_arrays()
        self.radon()
