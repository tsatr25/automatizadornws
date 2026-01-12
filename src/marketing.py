import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class TrackingGenerator:
    @staticmethod
    def generate_tracking(url, channel, campaign, **kwargs):
        """
        Genera la URL final trackeada según el canal.
        Canales soportados: 'push_n27', 'social_a2', 'newsletter_n1'
        """
        if not url: return ""
        
        # Limpieza base
        base_url = url.split("?")[0]
        
        if channel == "push_n27":
            return TrackingGenerator._generate_n27(base_url, campaign, **kwargs)
        elif channel == "social_a2":
            return TrackingGenerator._generate_a2(base_url, campaign, **kwargs)
        else:
            return url

    @staticmethod
    def _generate_n27(base_url, campaign, source="APP", product="Entradas", date_str=None, **kwargs):
        """
        Atrápalo N27 (Push/Web)
        atr_trk=N27-{YYYYMMDD}_{Campaña}-COM_{DDMMYY}_{Producto}_{Source}_{Campaña}
        &utm_source={app/web}&utm_medium=push&utm_campaign={Campaña}
        """
        today = time.strftime("%Y%m%d")
        today_short = time.strftime("%d%m%y")
        
        # Si el usuario pasó fecha manual (formato YYYY-MM-DD), la usamos
        if date_str and date_str.strip():
            try:
                # El navegador suele enviar YYYY-MM-DD
                if "-" in date_str:
                    dt_obj = time.strptime(date_str, "%Y-%m-%d")
                else:
                    dt_obj = time.strptime(date_str, "%Y%m%d")
                today = time.strftime("%Y%m%d", dt_obj)
                today_short = time.strftime("%d%m%y", dt_obj)
            except:
                pass # Fallback a current date
        
        camp_clean = campaign.strip().replace(" ", "")
        
        # Construcción ATR_TRK
        # Ejemplo: N27-20251211_ItalianBrainrots-COM_111225_Entradas_APP_ItalianBrainrots
        atr_trk = f"N27-{today}_{camp_clean}-COM_{today_short}_{product}_{source}_{camp_clean}"
        
        # Construcción UTMs
        # source: app o web (según input, lo pasamos a minúsculas para utm)
        utm_source = source.lower() if source.lower() in ["app", "web"] else "app"
        
        params = {
            "atr_trk": atr_trk,
            "utm_source": utm_source,
            "utm_medium": "push",
            "utm_campaign": campaign
        }
        
        return TrackingGenerator._append_params(base_url, params)

    @staticmethod
    def _generate_a2(base_url, campaign, social_network="instagram", **kwargs):
        """
        Atrápalo A2 (Social Media)
        Estructura: A2-{Código}-{Plataforma}
        Código: 3589 (FB/IG), 6569 (TikTok)
        """
        social_network = social_network.lower()
        if social_network in ["instagram", "facebook"]:
            code = "3589"
            platform_name = "Instagram" if social_network == "instagram" else "Facebook"
        elif social_network == "tiktok":
            code = "6569"
            platform_name = "TikTok"
        else:
            code = "A2"
            platform_name = social_network.capitalize()

        atr_trk = f"A2-{code}-{platform_name}"
        
        params = {
            "atr_trk": atr_trk,
            "utm_source": "meta",
            "utm_medium": "social_cpc",
            "utm_campaign": campaign
        }
        
        return TrackingGenerator._append_params(base_url, params)

    @staticmethod
    def _append_params(base_url, params):
        """Helper para añadir parametros a una URL limpiamente"""
        parsed = urlparse(base_url)
        query = parse_qs(parsed.query)
        
        # Merge de params nuevos
        for k, v in params.items():
            query[k] = [v]
            
        new_query = urlencode(query, doseq=True)
        
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))


class ImageResizer:
    @staticmethod
    def resize_atrapalo_url(url, width=None, quality=75):
        """
        Modifica URL de CDN Atrápalo para añadir ?auto=avif&width=X&quality=Y
        """
        if not url or "atrapalo.com" not in url:
            return url
            
        # Parseamos para no perder otros params si fuera necesario, 
        # aunque el CDN suele machacarlos.
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        
        # Lógica de usuario:
        # ?auto=avif&width={width}&quality={quality}
        
        query["auto"] = ["avif"]
        query["quality"] = [str(quality)]
        
        if width and str(width).strip():
            query["width"] = [str(width)]
        else:
            # Si el usuario no pone width, ¿quitamos el param o dejamos original?
            # Asumimos que si está vacío, no forzamos width.
            pass
            
        new_query = urlencode(query, doseq=True)
        
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
