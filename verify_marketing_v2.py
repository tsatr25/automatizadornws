import sys
import os
import time

# Add src to path
sys.path.append(os.getcwd())

from src.marketing import TrackingGenerator

def test_refined_tracking():
    print("--- Testing Refined Tracking ---")
    url = "https://www.atrapalo.com/entradas/test/"
    
    # 1. Test N27 con fecha manual y producto custom
    print("\nTesting N27 manual date & custom product:")
    n27 = TrackingGenerator.generate_tracking(
        url, "push_n27", "CampañaMix", 
        source="WEB", product="Conciertos",
        date_str="2026-05-20"
    )
    print(f"N27 Result: {n27}")
    if "atr_trk=N27-20260520" in n27 and "Conciertos" in n27:
        print("✅ N27 Refined OK")
    else:
        print("❌ N27 Refined FAIL")

    # 2. Test A2 - Instagram (Code 3589)
    print("\nTesting A2 Instagram (3589):")
    a2_ig = TrackingGenerator.generate_tracking(url, "social_a2", "SocialCampaign", social_network="instagram")
    print(f"A2 IG Result: {a2_ig}")
    if "atr_trk=A2-3589-Instagram" in a2_ig and "utm_source=meta" in a2_ig and "utm_medium=social_cpc" in a2_ig:
        print("✅ A2 Instagram OK")
    else:
        print("❌ A2 Instagram FAIL")

    # 3. Test A2 - TikTok (Code 6569)
    print("\nTesting A2 TikTok (6569):")
    a2_tk = TrackingGenerator.generate_tracking(url, "social_a2", "SocialCampaign", social_network="tiktok")
    print(f"A2 TikTok Result: {a2_tk}")
    if "atr_trk=A2-6569-TikTok" in a2_tk:
        print("✅ A2 TikTok OK")
    else:
        print("❌ A2 TikTok FAIL")

if __name__ == "__main__":
    test_refined_tracking()
