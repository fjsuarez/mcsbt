import pandas as pd
import holidays

import pytorch_lightning as pl
from pytorch_lightning.callbacks import EarlyStopping, LearningRateMonitor
from pytorch_lightning.loggers import TensorBoardLogger
from lightning.pytorch import Trainer
from lightning.pytorch.callbacks import ModelCheckpoint
from pytorch_forecasting import Baseline, TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import MAE, SMAPE, PoissonLoss, QuantileLoss
from pytorch_forecasting.models.temporal_fusion_transformer.tuning import optimize_hyperparameters


price_df = pd.read_csv("price_data.csv",
                       parse_dates=["GMT Time"],
                       na_values=['No Data Available']
                       )
price_df.columns = ["Time", "DA Price", "Intraday Price"]
# price_df.set_index("Time", inplace=True)
# price_df.rename_axis("Series", axis="columns", inplace=True)

generation_df = pd.read_csv("generation_data.csv",
                            parse_dates=["GMT Time"],
                            na_values=["No Data Available"])
generation_df.columns = ["Time",
                         "Biomass",
                         "Gas",
                         "Hard Coal",
                         "Oil",
                         "Hydro Pumped Storage",
                         "Hydro Run-of-River",
                         "Nuclear",
                         "Solar",
                         "Wind Onshore",
                         "Wind Offshore"]
# generation_df.set_index("Time", inplace=True)
# generation_df.rename_axis("Series", axis="columns", inplace=True)

demand_load_df = pd.read_csv("demand_load_data.csv",
                             parse_dates=["GMT Time"],
                             na_values=["No Data Available"])
demand_load_df.columns = ["Time", "Loss of Load Prob", "Actual Total Load", "Demand Outturn"]
# demand_load_df.set_index("Time", inplace=True)
# demand_load_df.rename_axis("Series", axis="columns", inplace=True)

balancing_df = pd.read_csv("balancing_data.csv",
                           parse_dates=["GMT Time"],
                           na_values=['No Data Available']
                           )
balancing_df.columns = ["Time",
                        "System Price",
                        "NIV Outturn",
                        "BM Bid Acceptances",
                        "BM Offer Acceptances",
                        "BSAD Volume Turn Up",
                        "BSAD Volume Turn Down",
                        "BSAD Volume Total",
                        "Intraday Volume"]
# balancing_df.set_index("Time", inplace=True)
# balancing_df.rename_axis("Series", axis="columns", inplace=True)

# price_df
# demand_load_df
# generation_df
# balancing_df

merged_df = price_df.merge(demand_load_df, on='Time') \
                    .merge(generation_df, on='Time') \
                    .merge(balancing_df, on='Time')

merged_df.interpolate(method='linear', inplace=True)
merged_df.set_index("Time", inplace=True)

# Extracting day, month, year, day of the week
merged_df['day'] = merged_df.index.day
merged_df['month'] = merged_df.index.month
merged_df['year'] = merged_df.index.year
merged_df['day_of_week'] = merged_df.index.dayofweek

# Check if it is weekend
merged_df['is_weekend'] = merged_df['day_of_week'] >= 5

# Check if it is a holiday in the UK
uk_holidays = holidays.UK()
merged_df['is_holiday'] = merged_df.index.to_series().apply(lambda x: x in uk_holidays)

day_of_week_map = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
}

merged_df['day_of_week'] = merged_df['day_of_week'].map(day_of_week_map)

is_weekend_map = {
    True: 'weekend',
    False: 'weekday'
}

# Map the boolean is_weekend to 'weekend' and 'weekday'
merged_df['is_weekend'] = merged_df['is_weekend'].map(is_weekend_map)

is_holiday_map = {
    True: 'holiday',
    False: 'non-holiday'
}

# Map the boolean is_weekend to 'weekend' and 'weekday'
merged_df['is_holiday'] = merged_df['is_holiday'].map(is_holiday_map)

natural_gas_price_uk = pd.read_csv("markets_historical_nguk_com.csv")
natural_gas_price_uk['Date'] = pd.to_datetime(natural_gas_price_uk['Date'], dayfirst=True)
natural_gas_price_uk.set_index('Date', inplace=True)
natural_gas_price_uk = natural_gas_price_uk.sort_index(ascending=True)
first_row = natural_gas_price_uk.iloc[0]
first_row
new_index = pd.to_datetime('2018-01-01 00:00:00')
natural_gas_price_uk.loc[new_index] = first_row
natural_gas_price_uk.sort_index(inplace=True)
natural_gas_price_uk = natural_gas_price_uk.reindex(merged_df.index, method='ffill')
natural_gas_price_uk = natural_gas_price_uk.drop(columns=['Symbol'])
natural_gas_price_uk = natural_gas_price_uk.add_prefix('NGUK ')

merged_df = merged_df.merge(natural_gas_price_uk, left_index=True, right_index=True, how='left')

natural_gas_price_eu = pd.read_csv("markets_historical_ngeu_com.csv")
natural_gas_price_eu['Date'] = pd.to_datetime(natural_gas_price_eu['Date'], dayfirst=True)
natural_gas_price_eu.set_index('Date', inplace=True)
natural_gas_price_eu = natural_gas_price_eu.sort_index(ascending=True)
first_row = natural_gas_price_eu.iloc[0]
first_row
new_index = pd.to_datetime('2018-01-01 00:00:00')
natural_gas_price_eu.loc[new_index] = first_row
natural_gas_price_eu.sort_index(inplace=True)
natural_gas_price_eu = natural_gas_price_eu.reindex(merged_df.index, method='ffill')
natural_gas_price_eu = natural_gas_price_eu.drop(columns=['Symbol'])
natural_gas_price_eu = natural_gas_price_eu.add_prefix('NGEU ')

merged_df = merged_df.merge(natural_gas_price_eu, left_index=True, right_index=True, how='left')

# Reset the index and turn it into a column
merged_df = merged_df.reset_index()
merged_df = merged_df.rename(columns={'index': 'Time'})

merged_df = merged_df.reset_index()
merged_df = merged_df.rename(columns={'index': 'time_idx'})

merged_df['group_id'] = 0

max_encoder_length = 96  # e.g., past 2 days
max_prediction_length = 48  # Next 48 half-hour intervals
training_cutoff = merged_df["time_idx"].max() - max_prediction_length

training = TimeSeriesDataSet(
    data=merged_df[merged_df["time_idx"] <= training_cutoff],
    time_idx="time_idx",
    target="System Price",
    group_ids=["group_id"],
    max_encoder_length=max_encoder_length,
    max_prediction_length=max_prediction_length, 
    min_encoder_length=max_encoder_length // 2,  
    min_prediction_length=24, 
    static_categoricals=[],
    static_reals=[],
    time_varying_known_categoricals=["day_of_week", "is_weekend", "is_holiday"],
    time_varying_known_reals=["day", "month", "year", "NGUK Open", "NGUK High", "NGUK Low", "NGUK Close", 
                               "NGEU Open", "NGEU High", "NGEU Low", "NGEU Close"],
    time_varying_unknown_categoricals=[], 
    time_varying_unknown_reals=[
        "DA Price",
        "Intraday Price",
        "Loss of Load Prob",
        "Actual Total Load",
        "Demand Outturn",
        "Biomass",
        "Gas",
        "Hard Coal",
        "Oil",
        "Hydro Pumped Storage",
        "Hydro Run-of-River",
        "Nuclear",
        "Solar",
        "Wind Onshore",
        "Wind Offshore",
        "NIV Outturn",
        "BM Bid Acceptances",
        "BM Offer Acceptances",
        "BSAD Volume Turn Up",
        "BSAD Volume Turn Down",
        "BSAD Volume Total",
        "Intraday Volume",
    ],
    target_normalizer=GroupNormalizer(groups=["group_id"], transformation="relu"),
)

# create validation set (predict=True) which means to predict the last max_prediction_length points in time
# for each series
validation = TimeSeriesDataSet.from_dataset(training, merged_df, predict=True, stop_randomization=True)

# create dataloaders for model
batch_size = 64  # set this between 32 to 128
train_dataloader = training.to_dataloader(train=True, batch_size=batch_size, num_workers=21)
val_dataloader = validation.to_dataloader(train=False, batch_size=batch_size * 10, num_workers=21)

tft = TemporalFusionTransformer.from_dataset(
    training,
    learning_rate=0.03,
    hidden_size=16,
    attention_head_size=1,
    dropout=0.1,
)

checkpoint_callback = ModelCheckpoint(
    dirpath="checkpoints",
    filename="tft_checkpoint",
    save_top_k=1,
    monitor="val_loss",  # Monitor validation loss
    mode="min",
)

trainer = Trainer(
    max_epochs=30,
    accelerator='gpu',
    callbacks=[checkpoint_callback],
    )
trainer.fit(
    tft,
    train_dataloaders=train_dataloader,
    val_dataloaders=val_dataloader,
)

trainer.save_checkpoint("tft_checkpoint.ckpt")