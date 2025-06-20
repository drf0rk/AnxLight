# SDXL MODELS
sdxl_model_data = {
    "uberRealisticPornMerge-xlV6Final-inpainting   BEST SO FAR!!! - PonyXL-Hybrid v1": {"url": "https://civitai.com/api/download/models/1024962", "name": "uberrealisticpornmerge_ponyxlHybridV1.safetensors", "inpainting": True}, # Assuming inpainting based on name
    "lustifySDXLNSFW_oltINPAINTING": {"url": "https://huggingface.co/RandomGulag/lustifySDXLNSFW_oltINPAINTING/resolve/main/lustifySDXLNSFW_oltINPAINTING.safetensors", "name": "lustifySDXLNSFW_oltINPAINTING.safetensors", "inpainting": True},
    "PornMaster-Pro \\u8272\\u60c5\\u5927\\u5e08 - SDXL - SDXL-V2-VAE": {"url": "https://civitai.com/api/download/models/1167499", "name": "pornmasterProSDXL_sdxlV2VAE.safetensors"},
    "True Amateur Feeling XL - v2": {"url": "https://civitai.com/api/download/models/907265", "name": "trueAmateurFeelingXL_v2.safetensors"},
    "Sippy": {"url": "https://huggingface.co/Red1618/Zhu/resolve/main/Sippy.safetensors?download=true", "name": "Sippy.safetensors"},
    "SDXL-DWXL": {"url": "https://huggingface.co/Remphanstar/Rojos/resolve/main/SDXL-DWXL.fp16.safetensors", "name": "SDXL-DWXL.fp16.safetensors"},
    "PornMaster-\\u8272\\u60c5\\u5927\\u5e08 - V7-FP16-VAE": {"url": "https://civitai.com/api/download/models/938228", "name": "pornmaster_v7FP16VAE.safetensors"},
}

# SDXL VAES
sdxl_vae_data = {
    "Pony Standard VAE - V1.0": {"url": "https://civitai.com/api/download/models/785437", "name": "ponyStandardVAE_v10.safetensors"},
    "FIX FP16 Errors SDXL - Lower Memory use! --- sdxl-vae-fp16-fix by madebyollin - v1.0": {"url": "https://civitai.com/api/download/models/155933", "name": "fixFP16ErrorsSDXLLowerMemoryUse_v10.safetensors"},
    "SDXL VAE - SDXL-VAE": {"url": "https://civitai.com/api/download/models/333245", "name": "sdxlVAE_sdxlVAE.safetensors"},
}

# SDXL CONTROLNET
# For ControlNets, the value is a list of file dictionaries.
# 'name' key should be added if missing, derived from URL.
sdxl_controlnet_data = {
    "1. Kohya Controllite XL Blur": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_blur.safetensors", 'name': 'kohya_controllllite_xl_blur.safetensors'},
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_blur_anime.safetensors", 'name': 'kohya_controllllite_xl_blur_anime.safetensors'}
    ],
    "2. Kohya Controllite XL Canny": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_canny.safetensors", 'name': 'kohya_controllllite_xl_canny.safetensors'},
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_canny_anime.safetensors", 'name': 'kohya_controllllite_xl_canny_anime.safetensors'}
    ],
    "3. Kohya Controllite XL Depth": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_depth.safetensors", 'name': 'kohya_controllllite_xl_depth.safetensors'},
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_depth_anime.safetensors", 'name': 'kohya_controllllite_xl_depth_anime.safetensors'}
    ],
    "4. Kohya Controllite XL Openpose Anime": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_openpose_anime.safetensors", 'name': 'kohya_controllllite_xl_openpose_anime.safetensors'},
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_openpose_anime_v2.safetensors", 'name': 'kohya_controllllite_xl_openpose_anime_v2.safetensors'}
    ],
    "5. Kohya Controllite XL Scribble Anime": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_scribble_anime.safetensors", 'name': 'kohya_controllllite_xl_scribble_anime.safetensors'}
    ],
    "6. T2I Adapter XL Canny": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_xl_canny.safetensors", 'name': 't2i-adapter_xl_canny.safetensors'}
    ],
    "7. T2I Adapter XL Openpose": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_xl_openpose.safetensors", 'name': 't2i-adapter_xl_openpose.safetensors'}
    ],
    "8. T2I Adapter XL Sketch": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_xl_sketch.safetensors", 'name': 't2i-adapter_xl_sketch.safetensors'}
    ],
    "9. T2I Adapter Diffusers XL Canny": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_canny.safetensors", 'name': 't2i-adapter_diffusers_xl_canny.safetensors'}
    ],
    "10. T2I Adapter Diffusers XL Depth Midas": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_depth_midas.safetensors", 'name': 't2i-adapter_diffusers_xl_depth_midas.safetensors'}
    ],
    "11. T2I Adapter Diffusers XL Depth Zoe": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_depth_zoe.safetensors", 'name': 't2i-adapter_diffusers_xl_depth_zoe.safetensors'}
    ],
    "12. T2I Adapter Diffusers XL Lineart": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_lineart.safetensors", 'name': 't2i-adapter_diffusers_xl_lineart.safetensors'}
    ],
    "13. T2I Adapter Diffusers XL Openpose": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_openpose.safetensors", 'name': 't2i-adapter_diffusers_xl_openpose.safetensors'}
    ],
    "14. T2I Adapter Diffusers XL Sketch": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_sketch.safetensors", 'name': 't2i-adapter_diffusers_xl_sketch.safetensors'}
    ],
    "15. IP Adapter SDXL": [
        {'url': "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter_sdxl.safetensors", 'name': 'ip-adapter_sdxl.safetensors'}
    ],
    "16. IP Adapter SDXL VIT-H": [
        {'url': "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter_sdxl_vit-h.safetensors", 'name': 'ip-adapter_sdxl_vit-h.safetensors'}
    ],
    "17. Diffusers XL Canny Mid": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/diffusers_xl_canny_mid.safetensors", 'name': 'diffusers_xl_canny_mid.safetensors'}
    ],
    "18. Diffusers XL Depth Mid": [
        {'url': "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/diffusers_xl_depth_mid.safetensors", 'name': 'diffusers_xl_depth_mid.safetensors'}
    ],
    "19. Controlnet Union SDXL 1.0": [
        {'url': "https://huggingface.co/xinsir/controlnet-union-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors", 'name': "controlnet-union-sdxl-1.0.safetensors"}
    ],
    "20. Controlnet Union SDXL Pro Max": [
        {'url': "https://huggingface.co/xinsir/controlnet-union-sdxl-1.0/resolve/main/diffusion_pytorch_model_promax.safetensors", 'name': "controlnet-union-sdxl-promax.safetensors"}
    ]
}

# SDXL LORAS
# Merged from scripts/data/lora_data.py's "sdxl_loras"
sdxl_lora_data = {
    "BT Lowering Pants - Pony v1": [{'url': "https://civitai.com/api/download/models/393888", 'name': "BT_Lowering_Pants_Pony.safetensors"}],
    "Lesbian fingering - v1.0": [{'url': "https://civitai.com/api/download/models/1030934", 'name': "Lesbian_fingering.safetensors"}],
    "Yuri Mutual Masturbation - v1.0-XL": [{'url': "https://civitai.com/api/download/models/567342", 'name': "Yuri Mutual Masturbation.safetensors"}],
    "Real Pussy - Cameltoe - v3 XL": [{'url': "https://civitai.com/api/download/models/802232", 'name': "Pussy_Cameltoe_v3_XL.safetensors"}],
    "Striped Micro Lingerie PONY XL - v2.0": [{'url': "https://civitai.com/api/download/models/518802", 'name': "hud_str_ling_v2_XLP.safetensors"}],
    "Nudify XL: Better Bodies - v1 Lite": [{'url': "https://civitai.com/api/download/models/177674", 'name': "nudify_xl_lite.safetensors"}],
    "Fingering Under Clothes/Implied Masturbation | Concept LoRA | SDXL Pony - V1": [{'url': "https://civitai.com/api/download/models/427792", 'name': "Lunas-Implied-Fingering-SDXL-A1.safetensors"}],
    "NSFW POV All In One SDXL (Realistic/Anime/WD14 - 74MB Version Available) - v1.0 (Full - Recommended)": [{'url': "https://civitai.com/api/download/models/160240", 'name': "NsfwPovAllInOneLoraSdxl-000009.safetensors"}],
    "Masturbating Under Panties - v1.0-Pony": [{'url': "https://civitai.com/api/download/models/624818", 'name': "MASTURBATING UNDER PANTIES.safetensors"}],
    "Multiple XL Sliders - Age, weight, Hands, etc - age_pony": [{'url': "https://civitai.com/api/download/models/686514", 'name': "agepony8.pt"}],
    "\\u30af\\u30ed\\u30c3\\u30c1\\u305a\\u3089\\u3057/panties aside(XL,Pony) - v2.0 pony": [{'url': "https://civitai.com/api/download/models/1567868", 'name': "panty aside_pony_V2.0.safetensors"}],
    "School Swimsuit and Kneehighs / \\u30b9\\u30af\\u6c34\\u30cb\\u30fc\\u30bd - XLv1.0": [{'url': "https://civitai.com/api/download/models/478142", 'name': "school swimsuit kneehigh XL-v1.safetensors"}],
    "LEAKCORE (LEAKED NUDES STYLE, Realism, Amateur) - v1.0 (LUSTIFY)": [{'url': "https://civitai.com/api/download/models/1627770", 'name': "leaked_nudes_style_v1_fixed.safetensors"}],
    "Pony Amateur \\u2728 - Standard (V2)": [{'url': "https://civitai.com/api/download/models/717403", 'name': "zy_AmateurStyle_v2.safetensors"}],
    "Lesbian pussy licking - v1.0": [{'url': "https://civitai.com/api/download/models/859154", 'name': "Lesbian_pussy_licking.safetensors"}],
    "Real Pussy - Peach - Rear v2 XL": [{'url': "https://civitai.com/api/download/models/1604857", 'name': "Pussy_Peach_Rear_v2_XL.safetensors"}],
}