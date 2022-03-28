import streamlit as st
from tomograph import Tomograph
import matplotlib.pyplot as plt
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import UID
import tempfile


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
        progress = st.slider('Progress', 0, tom.n_views_stored)
        get_picture(tom.image_filtered_storage[progress])
        return tom.image_filtered_result
    else:
        st.subheader('Sinogram')
        get_picture(tom.filtered_sinogram)
        st.subheader('Inverse')
        get_picture(tom.image_result)
        st.subheader('Progress')
        progress = st.slider('Progress', 0, tom.n_views_stored)
        get_picture(tom.image_storage[progress])
        return tom.image_result


def show_data(ds):
    st.header('Data')
    pat_name = f'{ds.PatientName.given_name} {ds.PatientName.family_name}' if hasattr(ds, 'PatientName') else 'Unknown'
    st.write(f"Patient's Name: {pat_name}")
    st.write(f"Patient ID: {ds.PatientID if hasattr(ds, 'PatientID') else 'Unknown'}")
    st.write(f"Modality: {ds.Modality if hasattr(ds, 'Modality') else 'Unknown'}")
    st.write(f"Study Date: {ds.StudyDate if hasattr(ds, 'StudyDate') else 'Unknown'}")
    st.write(f"Image size: {ds.Rows} x {ds.Columns}")
    st.write(f"Pixel Spacing: {ds.PixelSpacing if hasattr(ds, 'PixelSpacing') else 'Unknown'}")


def save_dicom(picture):
    st.header('Save DICOM file')
    with st.form('Siema'):
        surname_name = st.text_input('Nazwisko i imię')
        pesel = st.text_input('PESEL')
        test_date = st.date_input('Data badania')
        comment = st.text_area('Komentarz')
        save_btn = st.form_submit_button('Save me!')
        if save_btn:
            suffix = '.dcm'
            filename_little_endian = tempfile.NamedTemporaryFile(suffix=suffix).name
            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = UID('1.2.840.10008.5.1.4.1.1.2')
            file_meta.MediaStorageSOPInstanceUID = UID("1.2.3")
            file_meta.ImplementationClassUID = UID("1.2.3.4")

            ds = FileDataset(filename_little_endian, {},
                             file_meta=file_meta, preamble=b"\0" * 128)

            ds.PatientName = surname_name
            ds.PatientID = pesel
            ds.ContentDate = test_date
            ds.PatientComments = comment

            ds.save_as(filename_little_endian)

