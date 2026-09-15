import pandas as pd


class DateParser:
    def parse(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        result = df.copy()
        # dayfirst=True: nuestras fechas vienen en formato día/mes/año
        # (ej. "02/04/2026" = 2 de abril de 2026). Sin esto, pandas asume
        # mes/día/año (estilo EEUU) y para días <=12 interpreta mal la
        # fecha SIN lanzar error (ej. "02/04/2026" se leería como 4 de
        # febrero en vez de 2 de abril).
        result[date_column] = pd.to_datetime(
            result[date_column], errors="raise", dayfirst=True
        )
        return result.sort_values(date_column).reset_index(drop=True)