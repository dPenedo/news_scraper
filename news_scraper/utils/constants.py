from datetime import datetime

now = datetime.now()
mes_y_anio = f"{now.strftime("%B")}-{now.year}"

CSV_FILENAME = f"data/{mes_y_anio}-titulares.csv"
LOG_FILENAME = f"data/{mes_y_anio}-titulares.log"
