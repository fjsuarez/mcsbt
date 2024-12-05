import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# Step 1: Load Data
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

df = balancing_df.interpolate(method='linear')

natural_gas_price_uk = pd.read_csv("markets_historical_nguk_com.csv", parse_dates=["Date"], dayfirst=True)
natural_gas_price_uk = natural_gas_price_uk.sort_values(by="Date", ascending=True).drop(columns=['Symbol']).set_index("Date")   

first_row = natural_gas_price_uk.iloc[0]
new_index = pd.to_datetime('2018-01-01 00:00:00')
natural_gas_price_uk.loc[new_index] = first_row
natural_gas_price_uk.sort_index(inplace=True)

natural_gas_price_uk = natural_gas_price_uk.reindex(balancing_df.set_index('Time').index, method='ffill')
natural_gas_price_uk = natural_gas_price_uk.reset_index()
natural_gas_price_uk = natural_gas_price_uk.rename(columns={'index': 'Time'})

df = df.merge(natural_gas_price_uk, on='Time')

df = df[df["Time"] >= "2023-04-01"]

# Step 3: Split Data
train_size = int(len(df) * 0.8)
train, test = df.iloc[:train_size], df.iloc[train_size:]

# # Assume p=1, d=1, q=1; P=1, D=1, Q=1, s=48
# # Step 7 & 8: Fit SARIMAX
model = SARIMAX(
    train['System Price'],
    exog=train['High'],
    order=(1,1,1),
    seasonal_order=(1,1,1,48),
    enforce_stationarity=False,
    enforce_invertibility=False
)
print('Fitting SARIMAX model...')
sarimax_model = model.fit(disp=False)
print(sarimax_model.summary())

import pickle

# Save the fitted model to a file
with open('sarimax_model.pkl', 'wb') as file:
    pickle.dump(sarimax_model, file)

# # Step 9: Diagnostics
# residuals = sarimax_model.resid
# plt.figure(figsize=(12,6))
# plt.plot(residuals)
# plt.title('Residuals')
# plt.show()
# plot_acf(residuals, lags=40)
# plt.show()
# sns.histplot(residuals, kde=True)
# plt.show()

# from statsmodels.stats.diagnostic import acorr_ljungbox
# lb_test = acorr_ljungbox(residuals, lags=[10], return_df=True)
# print(lb_test)

# # Step 10: Forecast
# n_forecast = len(test)
# exog_forecast = test['x']
# forecast = sarimax_model.get_forecast(steps=n_forecast, exog=exog_forecast)
# forecast_ci = forecast.conf_int()
# y_pred = forecast.predicted_mean

# plt.figure(figsize=(12,6))
# plt.plot(train.index, train['y'], label='Train')
# plt.plot(test.index, test['y'], label='Test')
# plt.plot(test.index, y_pred, label='Forecast', color='red')
# plt.fill_between(test.index, forecast_ci['lower y'], forecast_ci['upper y'], color='pink', alpha=0.3)
# plt.legend()
# plt.show()

# # Step 11: Evaluation
# mse = mean_squared_error(test['y'], y_pred)
# rmse = np.sqrt(mse)
# mae = mean_absolute_error(test['y'], y_pred)
# print(f'MSE: {mse}, RMSE: {rmse}, MAE: {mae}')

# # Step 12: Grid Search (Optional)
# import itertools

# p = d = q = range(0, 2)
# pdq = list(itertools.product(p, d, q))
# seasonal_pdq = [(x[0], x[1], x[2], 12) for x in list(itertools.product(p, d, q))]

# best_aic = np.inf
# best_order = None
# best_seasonal_order = None

# for param in pdq:
#     for seasonal_param in seasonal_pdq:
#         try:
#             temp_model = SARIMAX(
#                 train['y'],
#                 exog=train['x'],
#                 order=param,
#                 seasonal_order=seasonal_param,
#                 enforce_stationarity=False,
#                 enforce_invertibility=False
#             )
#             temp_results = temp_model.fit(disp=False)
#             if temp_results.aic < best_aic:
#                 best_aic = temp_results.aic
#                 best_order = param
#                 best_seasonal_order = seasonal_param
#         except:
#             continue

# print(f'Best SARIMAX{best_order}x{best_seasonal_order} - AIC:{best_aic}')

# # Step 13: Final Model
# final_model = SARIMAX(
#     df['y'],
#     exog=df['x'],
#     order=best_order,
#     seasonal_order=best_seasonal_order,
#     enforce_stationarity=False,
#     enforce_invertibility=False
# )
# final_results = final_model.fit(disp=False)
# print(final_results.summary())

# # Forecasting future periods (example: next 12 months)
# # Replace with actual future 'x' values
# future_exog = pd.DataFrame({'x': [/* future x values */]}, index=pd.date_range(start=df.index[-1] + pd.offsets.MonthBegin(), periods=12, freq='MS'))
# forecast_final = final_results.get_forecast(steps=12, exog=future_exog)
# forecast_final_ci = forecast_final.conf_int()

# plt.figure(figsize=(12,6))
# plt.plot(df.index, df['y'], label='Historical')
# plt.plot(future_exog.index, forecast_final.predicted_mean, label='Forecast', color='red')
# plt.fill_between(future_exog.index, forecast_final_ci['lower y'], forecast_final_ci['upper y'], color='pink', alpha=0.3)
# plt.legend()
# plt.show()

# # Save the model
# import joblib
# joblib.dump(final_results, 'sarimax_model.pkl')
