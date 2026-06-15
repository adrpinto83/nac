import { Service } from "@railway/cli";

export default [
  new Service({
    name: "nac",
    attributes: {
      dockerfile: "Dockerfile",
      buildCommand: "pip install -r requirements.txt",
      startCommand: "python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    }
  })
];
