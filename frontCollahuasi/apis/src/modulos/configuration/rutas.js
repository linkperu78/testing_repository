const express = require("express");

const { PythonShell } = require("python-shell");
const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const { readFileSync } = require("fs");
const { parse } = require("csv-parse/sync");
const createCsvWriter = require("csv-writer").createObjectCsvWriter;

const router = express.Router();

router.get("/getband", getband);
router.post("/updateband", updateband);
router.get("/getCredenciales", getCredenciales);
router.post("/postCredenciales", postCredenciales);
router.post("/updateCredenciales", updateCredenciales);
router.delete("/deleteCredenciales", deleteCredenciales);

async function getCredenciales(req, res, next) {
  try {
    const fileContent = readFileSync("./scripts/credenciales.csv", "utf-8");
    const csvContent = parse(fileContent, {
      columns: true,
    });
    await respuesta.success(req, res, csvContent, 200);
  } catch (error) {
    next(error);
  }
}

async function updateCredenciales(req, res, next) {
  // console.log(req.body);
  try {
    const csvWriter = createCsvWriter({
      path: "scripts/credenciales.csv",
      header: [
        // { id: "ip", title: "ip" },
        { id: "username", title: "username" },
        { id: "password", title: "password" },
      ],
    });
    const records = [];
    const fileContent = readFileSync("./scripts/credenciales.csv", "utf-8");
    const csvContent = parse(fileContent);

    csvContent.forEach((item, index) => {
      if (index !== 0) {
        if (item[0] === req.body.params.userpre && item[1] === req.body.params.passpre) {
          records.push({
            // ip: req.body.params.ip,
            username: req.body.params.user,
            password: req.body.params.pass,
          });
        } else {
          records.push({
            // ip: item[0],
            username: item[0],
            password: item[1],
          });
        }
      }
    });

    csvWriter.writeRecords(records);
    await respuesta.success(req, res, "", 200);
  } catch (error) {
    next(error);
  }
}

async function postCredenciales(req, res, next) {
  console.log(req.body);
  try {
    const csvWriter = createCsvWriter({
      path: "scripts/credenciales.csv",
      header: [
        // { id: "ip", title: "ip" },
        { id: "username", title: "username" },
        { id: "password", title: "password" },
      ],
    });
    const records = [];
    const fileContent = readFileSync("./scripts/credenciales.csv", "utf-8");
    const csvContent = parse(fileContent);

    csvContent.forEach((item, index) => {
      if (index !== 0) {
        records.push({
          // ip: item[0],
          username: item[0],
          password: item[1],
        });
      }
    });
    records.push({
      // ip: req.body.params.ip,
      username: req.body.params.user,
      password: req.body.params.pass,
    });
    csvWriter.writeRecords(records);
    await respuesta.success(req, res, "", 200);
  } catch (error) {
    next(error);
  }
}

async function deleteCredenciales(req, res, next) {
  try {
    const csvWriter = createCsvWriter({
      path: "scripts/credenciales.csv",
      header: [
        // { id: "ip", title: "ip" },
        { id: "username", title: "username" },
        { id: "password", title: "password" },
      ],
    });
    const records = [];
    const fileContent = readFileSync("./scripts/credenciales.csv", "utf-8");
    const csvContent = parse(fileContent);

    csvContent.forEach((item, index) => {
      if (index !== 0) {
        if (item[0] !== req.query.user && item[1] !== req.query.pass) {
          records.push({
            // ip: item[0],
            username: item[0],
            password: item[1],
          });
        }
      }
    });
    csvWriter.writeRecords(records);
    await respuesta.success(req, res, "", 200);
  } catch (error) {
    next(error);
  }
}

async function getband(req, res, next) {
  try {
    let items = [];
    let options = {
      mode: "text",
      pythonOptions: ["-u"],
      scriptPath: "scripts",
      args: [req.query.ip, req.query.user, req.query.pass],
    };

    try {
      await PythonShell.run("getband.py", options).then((messages) => {
        items = messages;
      });

      await respuesta.success(req, res, items, 200);
    } catch (error) {
      respuesta.error(req, res, "Error en el Python", 200);
    }
  } catch (error) {
    next(error);
  }
}
async function updateband(req, res, next) {
  try {
    let items = [];
    let options = {
      mode: "text",
      pythonOptions: ["-u"],
      scriptPath: "scripts",
      args: [req.body.ip, req.body.user, req.body.pass, req.body.band],
    };

    try {
      await PythonShell.run("updateband.py", options).then((messages) => {
        items = messages;
      });

      await respuesta.success(req, res, items, 200);
    } catch (error) {
      respuesta.error(req, res, "Error en el Python", 200);
    }
  } catch (error) {
    next(error);
  }
}

module.exports = router;
