import pydicom
import streamlit as st
from tomograph import Tomograph
import matplotlib.pyplot as plt
from pydicom.dataset import FileDataset, Dataset, validate_file_meta
from pydicom.uid import UID, generate_uid
from pydicom._storage_sopclass_uids import MRImageStorage
from datetime import datetime
import numpy as np


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
        progress = st.slider('Progress', 0, tom.n_views_stored-1)
        get_picture(tom.get_filtered_storage()[progress])
        return tom.get_filtered_result()
    else:
        st.subheader('Sinogram')
        get_picture(tom.get_sinogram())
        st.subheader('Inverse')
        get_picture(tom.get_result())
        st.subheader('Progress')
        progress = st.slider('Progress', 0, tom.n_views_stored-1)
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
    ds = Dataset()
    ds.MediaStorageSOPClassUID = MRImageStorage
    ds.MediaStorageSOPInstanceUID = generate_uid()
    ds.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    fd = FileDataset(path, {}, file_meta=ds, preamble=b'\0' * 128)
    fd.is_little_endian = True
    fd.is_implicit_VR = False

    fd.SOPClassUID = MRImageStorage
    fd.PatientName = 'Test^Firstname'
    fd.PatientID = '123456'
    now = datetime.now()
    fd.StudyDate = now.strftime('%Y%m%d')
    fd.PatientComments = 'None'

    fd.Modality = 'CT'
    fd.SeriesInstanceUID = generate_uid()
    fd.StudyInstanceUID = generate_uid()
    fd.FrameOfReferenceUID = generate_uid()

    fd.ImagesInAcquisition = '1'
    fd.Rows = image.shape[0]
    fd.Columns = image.shape[1]
    fd.InstanceNumber = 1

    fd.RescaleIntercept = '0'
    fd.RescaleSlope = '1'
    fd.PixelSpacing = r'1\1'
    fd.PhotometricInterpretation = 'MONOCHROME2'
    fd.PixelRepresentation = 1

    fd.ImageType = r'ORIGINAL\PRIMARY'

    fd.BitsStored = 16
    fd.BitsAllocated = 16
    fd.SamplesPerPixel = 1
    fd.HighBit = 15

    for key, value in meta.items():
        setattr(fd, key, value)

    validate_file_meta(fd.file_meta, enforce_standard=True)

    fd.PixelData = (image * 255).astype(np.uint16).tobytes()
    fd.save_as(path)


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
                PatientName=surname_name,
                PatientID=pesel,
                PatientComments=comment,
                StudyDate=test_date
            ))
