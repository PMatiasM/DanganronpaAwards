import express from "express";
import consign from "consign";
import cors from "cors";

export default () => {
  const app = express();
  app.use(express.urlencoded({ extended: true }));
  app.use(express.json());
  app.use(cors());
  consign().include("./routes").into(app);

  return app;
};
