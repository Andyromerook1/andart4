# pdf_metadata.py
"""
Extrae metadata de PDFs encontrados durante el rastreo (ej: "instrucciones
de pago" de una estafa). La metadata puede delatar al autor real, el
software usado, o la fecha real de creación — y alimenta el módulo de
correlación si el mismo autor/software aparece en varias campañas.
Requiere: pip install pikepdf
"""
import pikepdf
import io


class PDFMetadataExtractor:
    def extraer(self, contenido_bytes, origen="desconocido"):
        """
        contenido_bytes: el PDF descargado (resp.content, no resp.text).
        Devuelve un dict con los campos de metadata más reveladores.
        """
        try:
            pdf = pikepdf.open(io.BytesIO(contenido_bytes))
            docinfo = pdf.docinfo
            meta = {
                "origen": origen,
                "autor": str(docinfo.get("/Author", "")) or None,
                "creador": str(docinfo.get("/Creator", "")) or None,
                "productor": str(docinfo.get("/Producer", "")) or None,
                "fecha_creacion": str(docinfo.get("/CreationDate", "")) or None,
                "fecha_modificacion": str(docinfo.get("/ModDate", "")) or None,
                "titulo": str(docinfo.get("/Title", "")) or None,
            }
            pdf.close()
            # Filtra campos vacíos
            return {k: v for k, v in meta.items() if v}
        except Exception as e:
            print(f"⚠️ Error leyendo metadata de PDF ({origen[:50]}): {e}")
            return {}
