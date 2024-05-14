from PIL import Image
import streamlit as st
import wave

# Convert encoding data into 8-bit binary
def genData(data):
    newd = [format(ord(i), '08b') for i in data]
    return newd

# Pixels are modified according to the 8-bit binary data and finally returned
def modPix(pix, data):
    datalist = genData(data)
    lendata = len(datalist)
    imdata = iter(pix)

    for i in range(lendata):
        pix = [value for value in imdata.__next__()[:3] +
                            imdata.__next__()[:3] +
                            imdata.__next__()[:3]]

        for j in range(0, 8):
            if (datalist[i][j] == '0' and pix[j] % 2 != 0):
                pix[j] -= 1
            elif (datalist[i][j] == '1' and pix[j] % 2 == 0):
                if (pix[j] != 0):
                    pix[j] -= 1
                else:
                    pix[j] += 1

        if (i == lendata - 1):
            if (pix[-1] % 2 == 0):
                if (pix[-1] != 0):
                    pix[-1] -= 1
                else:
                    pix[-1] += 1
        else:
            if (pix[-1] % 2 != 0):
                pix[-1] -= 1

        pix = tuple(pix)
        yield pix[0:3]
        yield pix[3:6]
        yield pix[6:9]

# Encode data into image
def encode_image(img, data):
    newimg = img.copy()
    w = newimg.size[0]
    encode_data = modPix(newimg.getdata(), data)
    newimg.putdata(list(encode_data))
    return newimg

# Decode the data in the image
def decode_image(img):
    image = Image.open(img, 'r')
    data = ''
    imgdata = iter(image.getdata())
    while True:
        pixels = [value for value in imgdata.__next__()[:3] +
                                imgdata.__next__()[:3] +
                                imgdata.__next__()[:3]]
        binstr = ''
        for i in pixels[:8]:
            if i % 2 == 0:
                binstr += '0'
            else:
                binstr += '1'
        data += chr(int(binstr, 2))
        if pixels[-1] % 2 != 0:
            return data

# Embed message into audio file
def embed(infile: str, message: str, outfile: str):
    song = wave.open(infile, mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))
    message = message + int((len(frame_bytes) - (len(message) * 8 * 8)) / 8) * '#'
    bits = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in message])))
    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 254) | bit
    frame_modified = bytes(frame_bytes)
    with wave.open(outfile, 'wb') as fd:
        fd.setparams(song.getparams())
        fd.writeframes(frame_modified)
    song.close()

# Extract message from audio file
def extract(file: str):
    song = wave.open(file, mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))
    extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
    message = "".join(chr(int("".join(map(str, extracted[i:i+8])), 2)) for i in range(0, len(extracted), 8))
    decoded = message.split("###")[0]
    song.close()
    return decoded

# Streamlit UI
st.title("Steganography")

option = st.selectbox("Choose steganography media:", ("Image", "Audio"))

if option == "Image":
    st.title("Image Steganography")
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "gif"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)

        st.subheader("Image Options")
        option = st.radio("Choose an option:", ("Encode", "Decode"))

        if option == "Encode":
            st.subheader("Encode Message in Image")
            message = st.text_input("Enter the message to hide:")
            if st.button("Encode"):
                if message:
                    new_image = encode_image(image, message)
                    st.image(new_image, caption='Encoded Image', use_column_width=True)
                    st.markdown("### Download Encoded Image")
                    st.image(new_image, output_format='PNG', use_column_width=True)
        elif option == "Decode":
            st.subheader("Decode Message from Image")
            if st.button("Decode"):
                decoded_message = decode_image(uploaded_file)
                st.text_area("Decoded Message", value=decoded_message, height=200)

elif option == "Audio":
    st.title("Audio Steganography")
    uploaded_file = st.file_uploader("Upload WAV Audio File", type=["wav"])
    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/wav')

        st.subheader("Audio Options")
        option = st.radio("Choose an option:", ("Encode", "Decode"))

        if option == "Encode":
            st.subheader("Encode Message in Audio")
            message = st.text_input("Enter the message to hide:")
            if st.button("Encode"):
                if message:
                    embed(uploaded_file, message, "output.wav")
                    st.success("Message hidden successfully!")
                    st.audio("output.wav", format='audio/wav')

        elif option == "Decode":
            st.subheader("Decode Message from Audio")
            if st.button("Decode"):
                decoded_message = extract(uploaded_file)
                st.info(f"Decoded Message: {decoded_message}")
