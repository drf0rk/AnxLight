# SD 1.5 MODELS
sd15_model_data = {
    "D5K6.0": {"url": "https://huggingface.co/Remphanstar/Rojos/blob/main/1.5-D5K6.0.safetensors", "name": "1.5-D5K6.0.safetensors"},
    "Merged amateurs - Mixed Amateurs": {"url": "https://civitai.com/api/download/models/179318", "name": "mergedAmateurs_mixedAmateurs.safetensors"},
    "PornMaster-Pro \u8272\u60c5\u5927\u5e08 - V10.1-VAE-inpainting - V10.1-VAE-inpainting": {"url": "https://civitai.com/api/download/models/937781", "name": "pornmasterProV101VAE_v101VAE-inpainting.safetensors"},
    "Merged Amateurs - Mixed Amateurs | Inpainting Model - v1.0": {"url": "https://civitai.com/api/download/models/188884", "name": "mergedAmateursMixed_v10-inpainting.safetensors"},
    "epiCRealism pureEvolution InPainting - v1.0": {"url": "https://civitai.com/api/download/models/95864", "name": "epicrealism_v10-inpainting.safetensors"},
    "fuego_v2_tkl4_fp26(1)": {"url": "https://huggingface.co/Remphanstar/Rojos/resolve/main/fuego_v2_tkl4_fp26(1).safetensors", "name": "fuego_v2_tkl4_fp26(1).safetensors"},
    "PornMaster-Pro \u8272\u60c5\u5927\u5e08 - FULL-V4-inpainting - FULL-V4-inpainting": {"url": "https://civitai.com/api/download/models/102709", "name": "pornmasterProFULLV4_fullV4-inpainting.safetensors"},
    "LazyMix+ (Real Amateur Nudes) - v4.0": {"url": "https://civitai.com/models/10961/lazymix-real-amateur-nudes", "name": "lazymixRealAmateur_v40.safetensors"},
    "PornMaster-Pro \u8272\u60c5\u5927\u5e08 - FULL-V5-inpainting - FULL-V5-inpainting": {"url": "https://civitai.com/api/download/models/176934", "name": "pornmasterProFULLV5_fullV5-inpainting.safetensors"},
    "SD.15-AcornMoarMindBreak": {"url": "https://huggingface.co/Remphanstar/Rojos/resolve/main/SD.15-AcornMoarMindBreak.safetensors", "name": "SD.15-AcornMoarMindBreak.safetensors"},
}

# SD 1.5 VAES
sd15_vae_data = {
    "vae-ft-mse-840000-ema-pruned | 840000 | 840k SD1.5 VAE - vae-ft-mse-840k": {"url": "https://civitai.com/api/download/models/311162", "name": "vaeFtMse840000EmaPruned_vaeFtMse840k.safetensors"},
    "ClearVAE(SD1.5) - v2.3": {"url": "https://civitai.com/api/download/models/88156", "name": "clearvaeSD15_v23.safetensors"},
}


# SD 1.5 CONTROLNET
sd15_controlnet_data = {
    "1. Openpose": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_openpose_fp16.yaml"}
    ],
    "2. Canny": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_canny_fp16.yaml"}
    ],
    "3. Depth": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11f1p_sd15_depth_fp16.yaml"}
    ],
    "4. Lineart": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_lineart_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_lineart_fp16.yaml"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15s2_lineart_anime_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15s2_lineart_anime_fp16.yaml"}
    ],
    "5. ip2p": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11e_sd15_ip2p_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11e_sd15_ip2p_fp16.yaml"}
    ],
    "6. Shuffle": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11e_sd15_shuffle_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11e_sd15_shuffle_fp16.yaml"}
    ],
    "7. Inpaint": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_inpaint_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_inpaint_fp16.yaml"}
    ],
    "8. MLSD": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_mlsd_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_mlsd_fp16.yaml"}
    ],
    "9. Normalbae": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_normalbae_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_normalbae_fp16.yaml"}
    ],
    "10. Scribble": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_scribble_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_scribble_fp16.yaml"}
    ],
    "11. Seg": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_seg_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_seg_fp16.yaml"}
    ],
    "12. Softedge": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_softedge_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_softedge_fp16.yaml"}
    ],
    "13. Tile": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors"},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11f1e_sd15_tile_fp16.yaml"}
    ]
}