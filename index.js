import customExpress from "./config/customExpress.js";
import "dotenv/config";

const app = customExpress();

const port = process.env.PORT;

app.listen(port, () => console.log(`API listening on port: ${port}`));
