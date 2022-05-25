import streamlit as st
from tomograph import Tomograph
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from pydicom.dataset import Dataset, FileMetaDataset

from tomograph import Tomograph


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
        get_picture(tom.get_filtered_sinogram())
        st.subheader('Filtered inverse')
        get_picture(tom.get_filtered_result())
        st.subheader('Progress')
        progress = st.slider('Progress', 0, tom.n_views_stored - 1)
        get_picture(tom.get_filtered_storage()[progress])
        return tom.get_filtered_result()
    else:
        st.subheader('Sinogram')
        get_picture(tom.get_sinogram())
        st.subheader('Inverse')
        get_picture(tom.get_result())
        st.subheader('Progress')
        progress = st.slider('Progress', 0, tom.n_views_stored - 1)
        get_picture(tom.get_storage()[progress])
        return tom.get_result()


def show_data(ds):
    st.header('Data')
    pat_name = f'{ds.PatientName.given_name} {ds.PatientName.family_name}' if hasattr(ds, 'PatientName') else 'Unknown'
    st.write(f"Patient's Name: {pat_name}")
    st.write(f"Content Date: {ds.ContentDate if hasattr(ds, 'ContentDate') else 'Unknown'}")
    st.write(f"Patient ID: {ds.PatientID if hasattr(ds, 'PatientID') else 'Unknown'}")
    st.write(f"Comments: {ds.PatientComments if hasattr(ds, 'PatientComments') else 'Unknown'}")
    st.write(f"Modality: {ds.Modality if hasattr(ds, 'Modality') else 'Unknown'}")
    st.write(f"Study Date: {ds.StudyDate if hasattr(ds, 'StudyDate') else 'Unknown'}")
    st.write(f"Image size: {ds.Rows} x {ds.Columns}")
    st.write(f"Pixel Spacing: {ds.PixelSpacing if hasattr(ds, 'PixelSpacing') else 'Unknown'}")


def read_dicom(path):
    from pydicom import dcmread
    ds = dcmread(path)
    # assume dicom metadata identifiers are uppercase
    keys = {x for x in dir(ds) if x[0].isupper()} - {'PixelData'}
    meta = {key: getattr(ds, key) for key in keys}
    image = ds.pixel_array
    return image, meta


def write_dicom(path, image, meta):
    file_meta = FileMetaDataset()

    file_meta.FileMetaInformationGroupLength = 192
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    file_meta.MediaStorageSOPInstanceUID = '1.3.6.1.4.1.5962.1.1.1.1.1.20040119072730.12322'
    file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'
    file_meta.ImplementationClassUID = '1.3.6.1.4.1.5962.2'
    file_meta.ImplementationVersionName = 'DCTOOL100'
    file_meta.SourceApplicationEntityTitle = 'CLUNIE1'

    ds = Dataset()
    ds.SpecificCharacterSet = 'ISO_IR 100'
    ds.ImageType = ['ORIGINAL', 'PRIMARY', 'AXIAL']

    dt = datetime.now()
    ds.ContentDate = dt.strftime('%Y-%m-%d')
    time_str = dt.strftime('%H:%M')
    ds.ContentTime = time_str

    ds.PatientName = 'Name^Surname'
    ds.PatientID = '123456789'

    for key, value in meta.items():
        setattr(ds, key, value)

    ds.StudyInstanceUID = '1.3.6.1.4.1.5962.1.2.1.20040119072730.12322'
    ds.SeriesInstanceUID = '1.3.6.1.4.1.5962.1.3.1.1.20040119072730.12322'
    ds.ImageComments = 'AAAAAAAAAA'

    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = 'MONOCHROME2'
    ds.Rows = image.shape[0]
    ds.Columns = image.shape[1]

    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.PixelPaddingValue = -2000
    ds.RescaleIntercept = "-1024.0"
    ds.RescaleSlope = "1.0"
    saved_image = image
    saved_image = saved_image / np.max(saved_image)
    saved_image = saved_image * (2 ^ 16 - 1)
    saved_image[saved_image < 0] = 0
    saved_image = saved_image.astype(np.uint16)
    ds.PixelData = saved_image

    ds.file_meta = file_meta
    ds.is_implicit_VR = True
    ds.is_little_endian = True
    ds.save_as(path, write_like_original=False)


def save_dicom(picture):
    st.header('Save as DICOM file')
    with st.form('save_me'):
        surname_name = st.text_input('Name and surname')
        pesel = st.text_input('PESEL')
        test_date = st.date_input('Content date')
        comment = st.text_area('Comment')
        save_btn = st.form_submit_button('Save me!')
        if save_btn:
            timestamp = str(datetime.timestamp(datetime.now())).split('.')[0]
            write_dicom(f'results/results_{timestamp}.dcm', picture, dict(
                PatientName=surname_name.replace(' ', '^'),
                PatientID=pesel,
                PatientComments=comment,
                StudyDate=test_date
            ))
