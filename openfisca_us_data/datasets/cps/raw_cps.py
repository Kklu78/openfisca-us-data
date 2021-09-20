from openfisca_us_data.utils import *
import requests
from io import BytesIO
from zipfile import ZipFile
import pandas as pd


@dataset
class RawCPS:
    name = "raw_cps"

    def generate(year: int):
        try:
            url = f"https://www2.census.gov/programs-surveys/cps/datasets/{year}/march/asecpub{str(year)[-2:]}csv.zip"
            response = requests.get(url, stream=True)
            total_size_in_bytes = int(
                response.headers.get("content-length", 200e6)
            )
            progress_bar = tqdm(
                total=total_size_in_bytes,
                unit="iB",
                unit_scale=True,
                desc="Downloading ASEC",
            )
        except Exception as e:
            raise FileNotFoundError(
                f"Attempted to download the ASEC for {year}, but encountered an error: {e.with_traceback()}"
            )
        try:
            year_code = str(year)[-2:]
            with BytesIO() as file, pd.HDFStore(RawCPS.file(year)) as storage:
                content_length_actual = 0
                for data in response.iter_content(int(1e6)):
                    progress_bar.update(len(data))
                    content_length_actual += len(data)
                    file.write(data)
                progress_bar.set_description("Downloaded ASEC")
                progress_bar.total = content_length_actual
                progress_bar.close()
                zipfile = ZipFile(file)
                with zipfile.open(f"pppub{year_code}.csv") as f:
                    storage["person"] = person = pd.read_csv(f).fillna(0)
                with zipfile.open(f"ffpub{year_code}.csv") as f:
                    storage["family"] = pd.read_csv(f).fillna(0)
                with zipfile.open(f"hhpub{year_code}.csv") as f:
                    storage["household"] = pd.read_csv(f).fillna(0)
                storage["tax_unit"] = create_tax_unit_table(person)
                storage["spm_unit"] = create_SPM_unit_table(person)
        except Exception as e:
            raise ValueError(
                f"Attempted to extract and save the CSV files, but encountered an error: {e.with_traceback()}"
            )


def create_tax_unit_table(person: pd.DataFrame) -> pd.DataFrame:
    TAX_UNIT_COLUMNS = [
        "ACTC_CRD",
        "AGI",
        "CTC_CRD",
        "EIT_CRED",
        "FED_RET",
        "FEDTAX_AC",
        "FEDTAX_BC",
        "MARG_TAX",
        "STATETAX_A",
        "STATETAX_B",
        "TAX_INC",
        "TAX_ID",
    ]
    return person[TAX_UNIT_COLUMNS].groupby(person.TAX_ID).sum()


def create_SPM_unit_table(person: pd.DataFrame) -> pd.DataFrame:
    SPM_UNIT_COLUMNS = [
        "ACTC",
        "CAPHOUSESUB",
        "CAPWKCCXPNS",
        "CHILDCAREXPNS",
        "CHILDSUPPD",
        "EITC",
        "ENGVAL",
        "EQUIVSCALE",
        "FAMTYPE",
        "FEDTAX",
        "FEDTAXBC",
        "FICA",
        "GEOADJ",
        "HAGE",
        "HHISP",
        "HMARITALSTATUS",
        "HRACE",
        "MEDXPNS",
        "NUMADULTS",
        "NUMKIDS",
        "NUMPER",
        "POOR",
        "POVTHRESHOLD",
        "RESOURCES",
        "SCHLUNCH",
        "SNAPSUB",
        "STTAX",
        "TENMORTSTATUS",
        "TOTVAL",
        "WCOHABIT",
        "WEIGHT",
        "WFOSTER22",
        "WICVAL",
        "WKXPNS",
        "WNEWHEAD",
        "WNEWPARENT",
        "WUI_LT15",
        "ID",
    ]
    return (
        person[["SPM_" + column for column in SPM_UNIT_COLUMNS]]
        .groupby(person.SPM_ID)
        .first()
    )
