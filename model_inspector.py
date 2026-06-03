import pickle
import sys

sys.path.append("cf")

with open("cf/outputs/models/best_cf_model_ncf.pkl", "rb") as f:
    data = pickle.load(f)

model = data["model"]

print(type(model))

print("\nAttributes:")
for k in vars(model):
    print("-", k, type(getattr(model, k)))