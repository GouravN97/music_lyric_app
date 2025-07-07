from diffusers import StableDiffusionPipeline
import torch

pipe= StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float32).to("cpu")

pipe.enable_attention_slicing()

image=pipe("a neon cityscape at dusk", num_interference_steps=20, height=512, width=512).images[0]
image.save("frame0.png")