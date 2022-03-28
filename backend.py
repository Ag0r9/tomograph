import streamlit as st
from tomograph import Tomograph
import matplotlib.pyplot as plt


def get_picture(picture):
    fig = plt.figure()
    plt.imshow(picture, cmap='gray')
    plt.axis("off")
    st.pyplot(fig)


def process_photo(img, step, no_of_detectors, bandwidth, filter_):
    st.header('Pictures')
    tom = Tomograph(img, step=step, no_of_detectors=no_of_detectors, bandwidth=bandwidth)
    tom.process()
    st.subheader('Original')
    get_picture(tom.original_image)
    if filter_:
        st.subheader('Filtered sinogram')
        get_picture(tom.filtered_sinogram)
        st.subheader('Filtered inverse')
        get_picture(tom.image_filtered_result)
        st.subheader('Progress')
        progress = st.slider('Step', 0, tom.n_views_stored)
        get_picture(tom.image_filtered_storage[progress])
    else:
        st.subheader('Sinogram')
        get_picture(tom.filtered_sinogram)
        st.subheader('Inverse')
        get_picture(tom.image_result)
        st.subheader('Progress')
        progress = st.slider('Step', 0, tom.n_views_stored)
        get_picture(tom.image_storage[progress])


def show_data(ds):
    st.header('Data')
    pat_name = ds.PatientName
    display_name = pat_name.family_name + ", " + pat_name.given_name
    st.write(f"Patient's Name: {display_name}")
    st.write(f"Patient ID: {ds.PatientID if hasattr(ds, 'PatientID') else 'Unknown'}")
    st.write(f"Modality: {ds.Modality if hasattr(ds, 'Modality') else 'Unknown'}")
    st.write(f"Study Date: {ds.StudyDate if hasattr(ds, 'StudyDate') else 'Unknown'}")
    st.write(f"Image size: {ds.Rows} x {ds.Columns}")
    st.write(f"Pixel Spacing: {ds.PixelSpacing if hasattr(ds, 'PixelSpacing') else 'Unknown'}")
