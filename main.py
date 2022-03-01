import streamlit as st
from PIL import Image, ImageOps
import matplotlib.pyplot as plt

st.title('Upload a photo')

uploaded_file = st.file_uploader('Choose an image...', type=['png', 'jpg', 'jpeg'])
if uploaded_file is not None:
    st.write('')
    st.write('Detecting...')
    # img = Image.open('data/jpgs/Kropka.jpg')
    img = Image.open(uploaded_file).convert('L')
    st.image(img)
