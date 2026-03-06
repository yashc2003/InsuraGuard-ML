import os
import numpy as np
import pandas as pd


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_dataset(n_rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    age = rng.integers(18, 80, n_rows)
    vehicle_age = rng.integers(0, 20, n_rows)
    claim_amount = rng.lognormal(mean=8.2, sigma=0.7, size=n_rows)
    annual_premium = rng.lognormal(mean=7.5, sigma=0.5, size=n_rows)
    incidents = rng.poisson(0.8, n_rows)
    witness_count = rng.integers(0, 4, n_rows)
    insurance_type = rng.choice(["auto", "health", "property"], p=[0.5, 0.3, 0.2], size=n_rows)

    policy_type = rng.choice(["basic", "standard", "premium"], p=[0.45, 0.4, 0.15], size=n_rows)
    collision_type = rng.choice(["rear", "side", "front", "none"], p=[0.2, 0.2, 0.15, 0.45], size=n_rows)
    police_report = rng.choice(["yes", "no"], p=[0.35, 0.65], size=n_rows)

    amount_ratio = claim_amount / (annual_premium + 1.0)

    linear = (
        -5.4
        + 0.03 * incidents
        + 0.22 * (insurance_type == "health")
        + 0.3 * (insurance_type == "property")
        + 0.35 * (policy_type == "basic")
        + 0.55 * (collision_type == "none")
        + 0.7 * (police_report == "no")
        + 0.18 * amount_ratio
        - 0.01 * age
        + 0.02 * vehicle_age
        - 0.1 * witness_count
    )

    fraud_prob = sigmoid(linear)
    is_fraud = rng.binomial(1, fraud_prob)

    df = pd.DataFrame(
        {
            "insurance_type": insurance_type,
            "age": age,
            "vehicle_age": vehicle_age,
            "claim_amount": claim_amount.round(2),
            "annual_premium": annual_premium.round(2),
            "incidents": incidents,
            "witness_count": witness_count,
            "policy_type": policy_type,
            "collision_type": collision_type,
            "police_report": police_report,
            "is_fraud": is_fraud,
        }
    )

    return df


def main() -> None:
    os.makedirs("data", exist_ok=True)
    df = generate_dataset()
    output_path = "data/insurance_claims.csv"
    df.to_csv(output_path, index=False)

    fraud_rate = df["is_fraud"].mean()
    print(f"Saved: {output_path}")
    print(f"Rows: {len(df)}")
    print(f"Fraud rate: {fraud_rate:.2%}")


if __name__ == "__main__":
    main()
