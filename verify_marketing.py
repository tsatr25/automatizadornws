import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.marketing import TrackingGenerator, ImageResizer

def test_tracking():
    print("--- Testing Tracking ---")
    url = "https://www.atrapalo.com/entradas/italian_e4936315/"
    
    # 1. N27 (Simulando webapp: pasando social_network y format sobrantes)
    n27 = TrackingGenerator.generate_tracking(
        url, "push_n27", "CampanaTest", 
        source="APP", product="Entradas",
        social_network="instagram", format="stories"
    )
    print(f"N27 Result: {n27}")
    if "atr_trk=N27-" in n27 and "utm_source=app" in n27:
        print("✅ N27 OK")
    else:
        print("❌ N27 FAIL")

    # 2. A2 (Simulando webapp: pasando source y product sobrantes)
    a2 = TrackingGenerator.generate_tracking(
        url, "social_a2", "CampanaSocial", 
        social_network="tiktok", format="stories",
        source="APP", product="Entradas"
    )
    print(f"A2 Result: {a2}")
    if "atr_trk=A2-" in a2 and "utm_source=tiktok" in a2:
        print("✅ A2 OK")
    else:
        print("❌ A2 FAIL")

def test_resizer():
    print("\n--- Testing Resizer ---")
    img_url = "https://cdn.atrapalo.com/test.jpg"
    
    # 1. Resize
    resized = ImageResizer.resize_atrapalo_url(img_url, width=1080, quality=80)
    print(f"Resized: {resized}")
    if "width=1080" in resized and "quality=80" in resized and "auto=avif" in resized:
        print("✅ Resizer OK")
    else:
        print("❌ Resizer FAIL")

if __name__ == "__main__":
    test_tracking()
    test_resizer()
