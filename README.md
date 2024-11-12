# LakotaNeuralDreams
Exploration of the Lakota Symbolic Dream Language using Artificial Intelligence and Electrophysiology 


# Dream Language Symbol Matching with CLIP

This project uses **CLIP** (Contrastive Language-Image Pretraining) to **match images of dream symbols with a test image** based on **cosine similarity**. The goal is to retrieve and rank symbolic representations similar to a given input image, leveraging embeddings from the CLIP model.

![lakota_CLIP_schematic](https://github.com/user-attachments/assets/7f85e176-c3d8-4bd7-8527-ca74c043e855)

## 🧩 Key Components

1. **CLIP Model and Processor Setup**  
   Loads a CLIP model and processor from **`laion/CLIP-ViT-H-14-laion2B-s32B-b79K`** for image and text feature extraction.

2. **Image to Vector Encoding (`img2vec`)**  
   - **Preprocesses images**: resizes and normalizes input images.
   - **Extracts feature embeddings** from the CLIP model's image encoder.

4. **Cosine Similarity Calculation**  
   A function to compute **cosine similarity** between two vectors, allowing us to measure closeness between the input image and each symbol image.

## 🖼️ Symbol Embedding and Matching

1. **Symbol Embedding Creation**  
   Loads all `*.png` images from the `dream_language` folder and **encodes each symbol into a vector**.

2. **Test Image Encoding and Similarity Matching**  
   - Encodes a test image into a vector.
   - Computes cosine similarity between the test image vector and each symbol vector.
   - **Ranks symbols** based on similarity scores.

## 📊 Visualization of Results

Displays the test image alongside the **top-matching symbols**, with similarity scores displayed above each symbol. This provides a **visual ranking** of symbols related to the test image.

![CLIP_drawing_example](https://github.com/user-attachments/assets/69c0ad9d-7d74-427d-8e3a-6cdbfb4688e8)
