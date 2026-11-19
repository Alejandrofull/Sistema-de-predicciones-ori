import pandas as pd

from app.ml.trainer import (
    ModelTrainer
)


dataframe = pd.DataFrame(
    {
        "fecha": pd.date_range(
            start="2025-01-01",
            periods=200,
            freq="D"
        ),
        "ventas": [
            100
            +
            (
                index
                % 7
            )
            * 3
            +
            (
                index
                * 0.05
            )
            for index
            in range(200)
        ]
    }
)


for lag in [
    1,
    7,
    14,
    28
]:

    dataframe[
        f"ventas_lag_{lag}"
    ] = (
        dataframe[
            "ventas"
        ]
        .shift(
            lag
        )
    )


shifted = (
    dataframe[
        "ventas"
    ]
    .shift(1)
)


for window in [
    7,
    14,
    28
]:

    dataframe[
        f"ventas_rolling_mean_{window}"
    ] = (
        shifted
        .rolling(
            window
        )
        .mean()
    )


dataframe[
    "month"
] = (
    dataframe[
        "fecha"
    ]
    .dt.month
)


dataframe[
    "day_of_week"
] = (
    dataframe[
        "fecha"
    ]
    .dt.dayofweek
)


dataframe = (
    dataframe
    .dropna()
    .reset_index(
        drop=True
    )
)


trainer = (
    ModelTrainer()
)


result = trainer.compare_all(
    dataframe=dataframe,
    date_column="fecha",
    target_column="ventas",
    test_ratio=0.20
)


print(
    "\n✅ MODELO GANADOR:"
)

print(
    result[
        "winner"
    ]
)


print(
    "\n✅ RANKING:"
)

for position, model_name in enumerate(
    result[
        "ranking"
    ],
    start=1
):

    metrics = (
        result[
            "results"
        ][
            model_name
        ][
            "metrics"
        ]
    )

    print(
        f"{position}. "
        f"{model_name} "
        f"- RMSE: "
        f"{metrics['rmse']:.4f} "
        f"- MAE: "
        f"{metrics['mae']:.4f} "
        f"- MAPE: "
        f"{metrics['mape']}"
    )


if result[
    "errors"
]:

    print(
        "\n⚠️ ERRORES:"
    )

    for model_name, error in (
        result[
            "errors"
        ].items()
    ):

        print(
            f"{model_name}: {error}"
        )