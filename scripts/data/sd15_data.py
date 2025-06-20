# SD 1.5 MODELS
sd15_model_data = {
    "D5K6.0": {"url": "https://huggingface.co/Remphanstar/Rojos/blob/main/1.5-D5K6.0.safetensors", "name": "1.5-D5K6.0.safetensors"},
    "Merged amateurs - Mixed Amateurs": {"url": "https://civitai.com/api/download/models/179318", "name": "mergedAmateurs_mixedAmateurs.safetensors"},
    "PornMaster-Pro \\u8272\\u60c5\\u5927\\u5e08 - V10.1-VAE-inpainting - V10.1-VAE-inpainting": {"url": "https://civitai.com/api/download/models/937781", "name": "pornmasterProV101VAE_v101VAE-inpainting.safetensors", "inpainting": True},
    "Merged Amateurs - Mixed Amateurs | Inpainting Model - v1.0": {"url": "https://civitai.com/api/download/models/188884", "name": "mergedAmateursMixed_v10-inpainting.safetensors", "inpainting": True},
    "epiCRealism pureEvolution InPainting - v1.0": {"url": "https://civitai.com/api/download/models/95864", "name": "epicrealism_v10-inpainting.safetensors", "inpainting": True},
    "fuego_v2_tkl4_fp26(1)": {"url": "https://huggingface.co/Remphanstar/Rojos/resolve/main/fuego_v2_tkl4_fp26(1).safetensors", "name": "fuego_v2_tkl4_fp26(1).safetensors"},
    "PornMaster-Pro \\u8272\\u60c5\\u5927\\u5e08 - FULL-V4-inpainting - FULL-V4-inpainting": {"url": "https://civitai.com/api/download/models/102709", "name": "pornmasterProFULLV4_fullV4-inpainting.safetensors", "inpainting": True},
    "LazyMix+ (Real Amateur Nudes) - v4.0": {"url": "https://civitai.com/models/10961/lazymix-real-amateur-nudes", "name": "lazymixRealAmateur_v40.safetensors"}, # Note: URL might need to be an API download link
    "PornMaster-Pro \\u8272\\u60c5\\u5927\\u5e08 - FULL-V5-inpainting - FULL-V5-inpainting": {"url": "https://civitai.com/api/download/models/176934", "name": "pornmasterProFULLV5_fullV5-inpainting.safetensors", "inpainting": True},
    "SD.15-AcornMoarMindBreak": {"url": "https://huggingface.co/Remphanstar/Rojos/resolve/main/SD.15-AcornMoarMindBreak.safetensors", "name": "SD.15-AcornMoarMindBreak.safetensors"},
}

# SD 1.5 VAES
sd15_vae_data = {
    "vae-ft-mse-840000-ema-pruned | 840000 | 840k SD1.5 VAE - vae-ft-mse-840k": {"url": "https://civitai.com/api/download/models/311162", "name": "vaeFtMse840000EmaPruned_vaeFtMse840k.safetensors"},
    "ClearVAE(SD1.5) - v2.3": {"url": "https://civitai.com/api/download/models/88156", "name": "clearvaeSD15_v23.safetensors"},
}


# SD 1.5 CONTROLNET
# For ControlNets, the value is a list of file dictionaries.
# 'name' key should be added if missing, derived from URL.
sd15_controlnet_data = {
    "1. Openpose": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose_fp16.safetensors", 'name': 'control_v11p_sd15_openpose_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_openpose_fp16.yaml", 'name': 'control_v11p_sd15_openpose_fp16.yaml'}
    ],
    "2. Canny": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny_fp16.safetensors", 'name': 'control_v11p_sd15_canny_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_canny_fp16.yaml", 'name': 'control_v11p_sd15_canny_fp16.yaml'}
    ],
    "3. Depth": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth_fp16.safetensors", 'name': 'control_v11f1p_sd15_depth_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11f1p_sd15_depth_fp16.yaml", 'name': 'control_v11f1p_sd15_depth_fp16.yaml'}
    ],
    "4. Lineart": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_lineart_fp16.safetensors", 'name': 'control_v11p_sd15_lineart_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_lineart_fp16.yaml", 'name': 'control_v11p_sd15_lineart_fp16.yaml'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15s2_lineart_anime_fp16.safetensors", 'name': 'control_v11p_sd15s2_lineart_anime_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15s2_lineart_anime_fp16.yaml", 'name': 'control_v11p_sd15s2_lineart_anime_fp16.yaml'}
    ],
    "5. ip2p": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11e_sd15_ip2p_fp16.safetensors", 'name': 'control_v11e_sd15_ip2p_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11e_sd15_ip2p_fp16.yaml", 'name': 'control_v11e_sd15_ip2p_fp16.yaml'}
    ],
    "6. Shuffle": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11e_sd15_shuffle_fp16.safetensors", 'name': 'control_v11e_sd15_shuffle_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11e_sd15_shuffle_fp16.yaml", 'name': 'control_v11e_sd15_shuffle_fp16.yaml'}
    ],
    "7. Inpaint": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_inpaint_fp16.safetensors", 'name': 'control_v11p_sd15_inpaint_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_inpaint_fp16.yaml", 'name': 'control_v11p_sd15_inpaint_fp16.yaml'}
    ],
    "8. MLSD": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_mlsd_fp16.safetensors", 'name': 'control_v11p_sd15_mlsd_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_mlsd_fp16.yaml", 'name': 'control_v11p_sd15_mlsd_fp16.yaml'}
    ],
    "9. Normalbae": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_normalbae_fp16.safetensors", 'name': 'control_v11p_sd15_normalbae_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_normalbae_fp16.yaml", 'name': 'control_v11p_sd15_normalbae_fp16.yaml'}
    ],
    "10. Scribble": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_scribble_fp16.safetensors", 'name': 'control_v11p_sd15_scribble_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_scribble_fp16.yaml", 'name': 'control_v11p_sd15_scribble_fp16.yaml'}
    ],
    "11. Seg": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_seg_fp16.safetensors", 'name': 'control_v11p_sd15_seg_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_seg_fp16.yaml", 'name': 'control_v11p_sd15_seg_fp16.yaml'}
    ],
    "12. Softedge": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_softedge_fp16.safetensors", 'name': 'control_v11p_sd15_softedge_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_softedge_fp16.yaml", 'name': 'control_v11p_sd15_softedge_fp16.yaml'}
    ],
    "13. Tile": [
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors", 'name': 'control_v11f1e_sd15_tile_fp16.safetensors'},
        {'url': "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11f1e_sd15_tile_fp16.yaml", 'name': 'control_v11f1e_sd15_tile_fp16.yaml'}
    ]
}

# SD 1.5 LORAS
# Merged from scripts/data/lora_data.py's "sd15_loras"
sd15_lora_data = {
    "female masturbation concepts - v2-LyCORIS-LoCon": [{'url': "https://civitai.com/api/download/models/50851", 'name': "concept-female_masturbation-v2.safetensors"}],
    "brothaman": [{'url': "https://huggingface.co/maximstar00/cute_pussy/resolve/main/brothaman.safetensors", 'name': "brothaman.safetensors"}],
    "Female masturbation - mastv1": [{'url': "https://civitai.com/api/download/models/44430", 'name': "mastv1.safetensors"}],
    "POV yuri cunnilingus - v1": [{'url': "https://civitai.com/api/download/models/58906", 'name': "qqq-cunnilingus_pov-v1.safetensors"}],
    "Cute Pussy  - v2.0": [{'url': "https://civitai.com/api/download/models/112806", 'name': "CutePussyVer2S.safetensors"}],
    "PornMaster-\\u81ea\\u62cd\\u3001\\u7a7f\\u8863\\u670d\\u81ea\\u6170\\u3001\\u88f8\\u4f53\\u81ea\\u6170\\u3001\\u900f\\u89c6\\u3001\\u9ad8\\u6f6e\\u8138& Selfie\\u3001clothed masturbation\\u3001naked masturbation\\u3001see-through \\u3001orgasm - V2-LYCORIS": [{'url': "https://civitai.com/api/download/models/344345", 'name': "clothed masturbation_V2.safetensors"}],
    "Female masturbation - v0.5": [{'url': "https://civitai.com/api/download/models/174016", 'name': "female_masturbation_v0.5.safetensors"}],
    "Female Masturbation [Boob Fondling and Fingering] - v1": [{'url': "https://civitai.com/api/download/models/20546", 'name': "masturbation-v1.safetensors"}],
    "PornMaster-Pro \\u8272\\u60c5\\u5927\\u5e08 - FULL-V4-inpainting - FULL-V4-inpainting": [{'url': "https://civitai.com/api/download/models/102709", 'name': "pornmasterProFULLV4_fullV4-inpainting.safetensors"}],
    "Hands Down Clothes - v1.0": [{'url': "https://civitai.com/api/download/models/144437", 'name': "hand-down-clothes.safetensors"}],
    "yuri cunnilingus - lora - v1.0": [{'url': "https://civitai.com/api/download/models/283261", 'name': "yuri_cunnilingus_v1.safetensors"}],
    "Sexy Catholic school uniform |anime+realistic| - v1.0": [{'url': "https://civitai.com/api/download/models/110260", 'name': "CatholicSchoolUniformDogu.safetensors"}],
    "Hand in panties - v0.82": [{'url': "https://civitai.com/api/download/models/170310", 'name': "hand_in_panties_v0.82.safetensors"}],
    "ppussy": [{'url': "https://huggingface.co/Remphanstar/Rojos/resolve/main/ppussy.safetensors", 'name': "ppussy.safetensors"}],
    "Sexy School Uniform | olaz - v1": [{'url': "https://civitai.com/api/download/models/169692", 'name': "sexyschooluniformv1.safetensors"}],
    "Labiaplasty (Innie Pussy Adjuster) [SD1.5 + SDXL] - v2.0": [{'url': "https://civitai.com/api/download/models/167994", 'name': "m99_labiaplasty_pussy_2.safetensors"}],
    "School Dress Collection By Stable Yogi - SF_School_Dress": [{'url': "https://civitai.com/api/download/models/332880", 'name': "SF_School_Dress_By_Stable_Yogi.safetensors"}],
    "Panties pulled aside fuck | Sex Lora 011 | Perfect - v1.0": [{'url': "https://civitai.com/api/download/models/63998", 'name': "panties_pulled_aside_fuck.v1.0.safetensors"}],
    "yuri cunnilingus - v4": [{'url': "https://civitai.com/api/download/models/58951", 'name': "qqq-yuri-cunnilingus-v4.safetensors"}],
    "Panties to side LoRA - v2": [{'url': "https://civitai.com/api/download/models/45127", 'name': "PantiesToSide-v2.safetensors"}],
}