from backend import process_photo, show_data, save_dicom

import skimage
import streamlit as st
import matplotlib.pyplot as plt
import pydicom


def get_picture(picture):
    fig = plt.figure()
    plt.imshow(picture, cmap='gray')
    plt.axis("off")
    st.pyplot(fig)


with st.sidebar:
    step = st.slider('Step', 1.0, 4.0, step=0.1)
    no_of_detectors = st.slider('Number of detectors', 60, 120)
    bandwidth = st.slider('Bandwidth', 90, 150)
    filter_ = st.checkbox('Filter')

st.header('Upload a photo')


uploaded_file = st.file_uploader('Choose an image...', type=['png', 'jpg', 'jpeg', 'dcm'])
if uploaded_file is not None:
    if uploaded_file.type == 'image/jpeg':
        img = skimage.io.imread(uploaded_file, as_gray=True)
    elif uploaded_file.type == 'application/octet-stream':
        ds = pydicom.dcmread(uploaded_file)
        show_data(ds)
        img = ds.pixel_array/255.0
    final_picture = process_photo(img, step, no_of_detectors, bandwidth, filter_)
    save_dicom(final_picture)
