// const transporter = require("../mail");
const mysql = require("mysql");
const config = require("../config");
// const condi = require("../const/constantes");
const md5 = require("md5");
const { createClient } = require("redis");
const { PythonShell } = require("python-shell");

const client = createClient({
  host: "127.0.0.1",
  port: 6379,
});

(async () => {
  await client.connect();
})();

client.on("connect", () => console.log("Redis Client Connected"));
client.on("error", (err) => console.log("Redis Client Connection Error", err));

const dbConfig = {
  host: config.mysql.host,
  user: config.mysql.user,
  password: config.mysql.password,
  database: config.mysql.database,
  connectionLimit: 20,
  queueLimit: 0,
};

let pool;

async function conecMySQL() {
  pool = mysql.createPool(dbConfig);
}
conecMySQL();

/*****************************************
 *************** DASHBOARD ***************
 ****************************************/

async function getAlarmToDashBoard(res) {
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.problema AS causa, a.ip, 
    a.detalle, a.estado AS status, b.tag AS name, b.rol AS subtipo, b.tipo, b.marca
    FROM eventos a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.fecha >= NOW() - INTERVAL 15 MINUTE AND a.urgente = 0
    ORDER BY fecha DESC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getAlarmRecurrentToDashBoard(res) {
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.problema AS causa, a.ip, 
    a.detalle, a.estado AS status, b.tag AS name, b.rol AS subtipo, b.tipo, b.marca, a.recurrencia
    FROM eventos a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.fecha >= NOW() - INTERVAL 6 HOUR AND a.urgente = 1
    ORDER BY fecha DESC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getAllOperability(res) {
  const response = await client.get("allOperability");
  if (response) return res.json(JSON.parse(response));
}

async function getAllOperabilityLastDay(res) {
  const response = await client.get("allOperabilityLastDay");
  if (response) return res.json(JSON.parse(response));
}

async function getKPIDashboard(query, res) {
  const response = await client.get("kpidashboard-" + query);
  if (response) return res.json(JSON.parse(response));
}

/*****************************************
 ****************** KPI ******************
 ****************************************/

async function getAllDataKPI(query, res) {
  const response = await client.get(query);
  if (response) return res.json(JSON.parse(response));
}

async function getCostWiredpeers(res) {
  const response = await client.get("kpiCostWired");
  if (response) return res.json(JSON.parse(response));
}

async function getCostWirelesspeers(res) {
  const response = await client.get("kpiCostWireless");
  if (response) return res.json(JSON.parse(response));
}

async function getAllLatency(res) {
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') as fecha, a.ip, a.latencia, b.tag AS name, b.tipo, b.rol AS subtipo 
    FROM latencia a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.fecha >= NOW() - INTERVAL 15 MINUTE
    ORDER BY a.fecha DESC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

/*****************************************
 *************** INSTAMESH ***************
 ****************************************/

async function getAllWirelessData(res) {
  const response = await client.get("AllWirelessData");
  if (response) return res.json(JSON.parse(response));
}

async function getAllWiredData(res) {
  const response = await client.get("AllWiredData");
  if (response) return res.json(JSON.parse(response));
}

async function getAllTempData(res) {
  const response = await client.get("AllTempData");
  if (response) return res.json(JSON.parse(response));
}

async function getAllCostData(res) {
  const response = await client.get("AllCostData");
  if (response) return res.json(JSON.parse(response));
}

async function getAllCostJRData(res) {
  const response = await client.get("AllCostJRData");
  if (response) return res.json(JSON.parse(response));
}

async function getAllWirelessDataByIP(res, ip) {
  const response = await client.get("WirelessData-" + ip);
  if (response) return res.json(JSON.parse(response));
  await pool.query(
    `SELECT a.ip, b.tag AS name, DATE_FORMAT(a.fecha,'%Y-%m-%d %H:%i:00') AS fecha, a.wireless
    FROM rajant_data a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.fecha > NOW() - INTERVAL 30 DAY AND a.ip = '${ip}'
    ORDER BY a.fecha ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("WirelessData-" + ip, JSON.stringify(result));

      client.expire("WirelessData-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllWiredDataByIP(res, ip) {
  const response = await client.get("WiredData-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT a.ip, b.tag AS name, DATE_FORMAT(a.fecha,'%Y-%m-%d %H:%i:00') AS fecha, a.wired
    FROM rajant_data a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.fecha > NOW() - INTERVAL 30 DAY AND a.ip = '${ip}'
    ORDER BY a.fecha ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("WiredData-" + ip, JSON.stringify(result));

      client.expire("WiredData-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllTempDataByIP(res, ip) {
  const response = await client.get("TempData-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(a.fecha,'%Y-%m-%d %H:%i:00') AS fecha, a.ip, a.valores
    FROM sensores a
    WHERE a.ip = '${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY
    ORDER BY a.fecha ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("TempData-" + ip, JSON.stringify(result));

      client.expire("TempData-" + ip, 300);

      res.json(result);
    }
  );
}

//wiredpeers - COSTO
async function getAllCostDataByIP(res, ip) {
  const response = await client.get("CostData-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, b.tag AS name, a.wired 
    FROM rajant_data a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.ip = '${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY
    GROUP BY a.fecha;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("CostData-" + ip, JSON.stringify(result));

      client.expire("CostData-" + ip, 300);

      res.json(result);
    }
  );
}

//wirelesspeers - COSTO
async function getAllCostJRDataByIP(res, ip) {
  const response = await client.get("CostJRData-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, b.tag AS name, a.wired 
    FROM  rajant_data a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.fecha > NOW() - INTERVAL 30 DAY a.ip ='${ip}'`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("CostJRData-" + ip, JSON.stringify(result));

      client.expire("CostJRData-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllIPS(res) {
  const response = await client.get("allIPInstamesh");
  if (response) return res.json(JSON.parse(response));
}

/*****************************************
 ************** INVENTARIO ***************
 ****************************************/

async function getAllData(tabla) {
  return new Promise((resolve, reject) => {
    pool.query(`SELECT * FROM ${tabla}`, (error, result) => {
      if (error) return reject(error);
      resolve(result);
    });
  });
}

async function addData(tabla, data) {
  return new Promise((resolve, reject) => {
    pool.query(`INSERT INTO ${tabla} SET ?`, data, (error, result) => {
      if (error) return reject(error);
      resolve(result);
    });
  });
}

async function editData(tabla, data) {
  return new Promise((resolve, reject) => {
    pool.query(
      `UPDATE ${tabla} SET ? WHERE id = ?`,
      [data, data.id],
      (error, result) => {
        if (error) return reject(error);
        resolve(result);
      }
    );
  });
}

async function deleteData(tabla, ip, id) {
  let querys = {
    cambium_data: `DELETE FROM cambium_data WHERE ip = '${ip}';`,
    clustering_data: `DELETE FROM clustering_data WHERE ip = '${ip}';`,
    eventos: `DELETE FROM eventos WHERE ip = '${ip}';`,
    latencia: `DELETE FROM latencia WHERE ip = '${ip}';`,
    LTE_data: `DELETE FROM LTE_data WHERE ip = '${ip}';`,
    inventario: `DELETE FROM inventario WHERE id = ${id};`,
    predicciones: `DELETE FROM predicciones WHERE ip = '${ip}';`,
    rajant_data: `DELETE FROM rajant_data WHERE ip = '${ip}';`,
    sensores: `DELETE FROM sensores WHERE ip = '${ip}';`,
    servidor_data: `DELETE FROM servidor_data WHERE ip = '${ip}';`,
    ubicacion_gps: `DELETE FROM ubicacion_gps WHERE ip = '${ip}';`,
  };
  let selectedQuery = querys[tabla];
  return new Promise((resolve, reject) => {
    pool.query(`${selectedQuery}`, (error, result) => {
      if (error) return reject(error);
      resolve(result);
    });
  });
}

async function getSubTypeInventory(res) {
  pool.query(`SELECT rol AS name FROM lista_rol;`, async (error, result) => {
    res.json(result);
  });
}

async function getTypeInventory(res) {
  pool.query(`SELECT tipo AS name FROM lista_tipo;`, async (error, result) => {
    res.json(result);
  });
}

async function getMarkInventory(res) {
  pool.query(
    `SELECT marca AS name FROM lista_marcas;`,
    async (error, result) => {
      res.json(result);
    }
  );
}

async function getSNMPInventory(res) {
  pool.query(`SELECT id AS name FROM snmp_conf;`, async (error, result) => {
    res.json(result);
  });
}

/*****************************************
 ***************** LOGIN *****************
 ****************************************/

async function getUserLogin(user, pass) {
  return new Promise((resolve, reject) => {
    pool.query(
      `SELECT count(user) AS valor, user, psswrd, rol FROM usuarios WHERE user = '${user}'`,
      (error, result) => {
        let finalArray = {};
        if (result[0].valor !== 0) {
          if (md5(pass) === result[0].psswrd) {
            finalArray = {
              user: result[0].user,
              status: "User Found",
              rol: result[0].rol,
            };
          } else {
            finalArray = { user: result[0].user, status: "Password Wrong" };
          }
        } else {
          finalArray = { user: result[0].user, status: "User Not Found" };
        }
        if (error) return reject(error);
        resolve(finalArray);
      }
    );
  });
}

/*****************************************
 ***************** MAPS ******************
 ****************************************/

async function getAllLatLngPMPSM(res) {
  const response = await client.get("LatLngPMPSM");
  if (response) return res.json(JSON.parse(response));
}

// async function getAllLatLngPMPSM2() {
//   return new Promise((resolve, reject) => {
//     pool.query(
//       `SELECT ip, gpsLat AS latitud, gpsLong AS longitud, hostname, marca, tipo, padre
//       FROM inventario
//       WHERE tipo = 'PMP' AND gpsLat NOT LIKE '+0%';`,
//       (error, result) => {
//         if (error) return reject(error);
//         resolve(result);
//       }
//     );
//   });
// }

async function getAllLatLngANY() {
  return new Promise((resolve, reject) => {
    pool.query(
      `SELECT b.ip, b.gpsLat AS latitud, b.gpsLong AS longitud, b.hostname, b.marca, b.tipo, b.padre, a.host_status AS status 
      FROM inventario b INNER JOIN status_history a ON b.ip = a.host_ip
      WHERE b.gpsLat NOT LIKE '+0%' AND b.gpsLat NOT LIKE '-0%' AND b.gpsLat != '' AND b.gpsLat !='0' AND a.resulttime > NOW() - INTERVAL 15 MINUTE - INTERVAL 2 HOUR;`,
      (error, result) => {
        if (error) return reject(error);
        resolve(result);
      }
    );
  });
}

async function getAllLatLngGPSTEST() {
  return new Promise((resolve, reject) => {
    // WHERE datetime >= NOW() - INTERVAL 15 MINUTE - INTERVAL 1 HOUR
    pool.query(
      `SELECT b.ip AS ip, b.lat AS latitud, b.lon AS longitud, b.datetime, a.hostname, a.tipo, a.marca, (SELECT c.host_status  FROM status_history c WHERE c.host_ip = a.ip ORDER BY resulttime DESC LIMIT 1) AS status
      FROM gps_test b INNER JOIN inventario a ON b.ip = a.ip 
      ORDER BY datetime DESC 
      LIMIT 2;`,
      (error, result) => {
        if (error) return reject(error);
        resolve(result);
      }
    );
  });
}

async function getAllLatLngPMPAP(res) {
  pool.query(
    `SELECT a.tag AS name, a.ip, a.tipo, a.gps
    FROM inventario a
    WHERE UPPER(a.tipo) = 'PMP-AP'`,
    (error, result) => {
      if (error) return reject(error);
      res.json(result);
    }
  );
}

async function getAllPolylines(res) {
  pool.query(
    `SELECT ip_fuente, ip_cliente
      FROM estructura_red`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getPositionHaulTrucks(res, ip) {
  const response = await client.get("positionHaultruck-" + ip);
  if (response) return res.json(JSON.parse(response));
  // a.ip = '${ip}' AND
  pool.query(
    `SELECT b.latencia, a.ip, DATE_FORMAT(a.fecha, "%Y-%m-%d %H:%i:00") AS fecha, a.latitud,a.longitud  
    FROM ubicacion_gps a INNER JOIN latencia b ON a.ip = b.ip
    WHERE a.ip = '${ip}' AND a.fecha >= NOW() - INTERVAL 13 HOUR AND DATE_FORMAT(a.fecha, "%Y-%m-%d %H:%i:00") =  DATE_FORMAT(b.fecha, "%Y-%m-%d %H:%i:00") 
    ORDER BY a.fecha DESC;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("positionHaultruck-" + ip, JSON.stringify(result));

      client.expire("positionHaultruck-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllHaulTrucks(res) {
  pool.query(
    `SELECT tag AS name, ip  
    FROM inventario WHERE UPPER(tipo) = 'HAULTRUCK'
    ORDER BY tag ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getAllHaulTrucksDrive(res) {
  const response = await client.get("getAllHaulTrucksDrive");
  if (response) return res.json(JSON.parse(response));
  // pool.query(
  //   `SELECT hostname, ip, marca
  //   FROM inventario
  //   WHERE tipo = 'Haultruck'
  //   ORDER BY hostname ASC;`,
  //   async (error, result) => {
  //     if (error) return console.log(error);
  //     res.json(result);
  //   }
  // );
}
// async function getAllHaulTrucksDrive2(res) {
//   pool.query(
//     `SELECT hostname, ip, marca
//     FROM inventario
//     WHERE observacion = 'drive'
//     ORDER BY hostname ASC;`,
//     async (error, result) => {
//       if (error) return console.log(error);
//       res.json(result);
//     }
//   );
// }

async function getPositionDrivesRajant(res, ip) {
  // const response = await client.get("positionDrives-" + ip);
  // if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(Datetime, "%Y-%m-%d %H:%i:00") AS fecha, gpsLat AS lat, gpsLong AS lon, port, cost, ipv4Address
    FROM tracking_rajant
    WHERE ip_rajant = '${ip}' AND gpsLat != '' AND Datetime >= '2024-06-27 14:53:59'
    ORDER BY Datetime DESC;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("positionHaultruckRajant-" + ip, JSON.stringify(result));

      client.expire("positionHaultruckRajant-" + ip, 300);

      res.json(result);
    }
  );
}

// async function getPositionDrives2(res, ip) {
//   // const response = await client.get("positionDrives-" + ip);
//   // if (response) return res.json(JSON.parse(response));

//   pool.query(
//     `SELECT DATE_FORMAT(Datetime, "%Y-%m-%d %H:%i:00") AS fecha, lat, lon, rssi, rsrp, rsrq
//     FROM tracking
//     WHERE IP = '${ip}' AND lat != '' AND Datetime >= NOW() - INTERVAL 12 HOUR - INTERVAL 2 HOUR
//     ORDER BY Datetime DESC;`,
//     async (error, result) => {
//       if (error) return console.log(error);
//       await client.set("positionHaultruck-" + ip, JSON.stringify(result));

//       client.expire("positionHaultruck-" + ip, 300);

//       res.json(result);
//     }
//   );
// }

async function getPositionDrives(res, ip) {
  pool.query(
    `SELECT b.latencia, a.ip, DATE_FORMAT(a.fecha, "%Y-%m-%d %H:%i:00") AS fecha, a.latitud,a.longitud
    FROM ubicacion_gps a INNER JOIN latencia b ON a.ip = b.ip
    WHERE  a.ip = '${ip}' AND a.fecha >= NOW() - INTERVAL 12 HOUR AND DATE_FORMAT(a.fecha, "%Y-%m-%d %H:%i:00") =  DATE_FORMAT(b.fecha, "%Y-%m-%d %H:%i:00")
    ORDER BY a.fecha DESC;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("positionHaultruck-" + ip, JSON.stringify(result));

      client.expire("positionHaultruck-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllLatLngRAJANT(res) {
  const response = await client.get("LatLngRAJANT");
  if (response) return res.json(JSON.parse(response));
}

// async function getCoverage(res) {
//   const response = await client.get("markers");
//   if (response) return res.json(JSON.parse(response));
// }

/*****************************************
 **************** PREDICT ****************
 ****************************************/

async function getAllPredictRXLVLData(res) {
  const response = await client.get("allPredictData");
  if (response) return res.json(JSON.parse(response));
}

async function getPredTableRXLVLData(ip, res) {
  const response = await client.get("PredTableRXLVLData-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(fecha, "%Y-%m-%d %H:%i:00") AS fecha, ip, tipo_prediccion AS causa, value AS detalle 
    FROM predicciones 
    WHERE ip = '${ip}' AND fecha > NOW() - INTERVAL 30 DAY AND UPPER(tipo_prediccion) LIKE ('%RX%')
    ORDER BY fecha DESC 
    LIMIT 10;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("PredTableRXLVLData-" + ip, JSON.stringify(result));

      client.expire("PredTableRXLVLData-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllRXLVLPredDataByIP(ip, res) {
  const response = await client.get("PredPredData-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(fecha, "%Y-%m-%d %H:%i:00") AS fecha, value AS kpi 
    FROM predicciones 
    WHERE ip = '${ip}' AND fecha > NOW() - INTERVAL 30 DAY AND UPPER(tipo_prediccion) LIKE ('%RX%') 
    ORDER BY fecha ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("PredPredData-" + ip, JSON.stringify(result));

      client.expire("PredPredData-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllRXLVLRealDataByIP(ip, res) {
  const response = await client.get("PredRealData-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, "%Y-%m-%d %H:%i:00") AS fecha, link_radio AS kpi 
    FROM cambium_data a
    WHERE ip = '${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY ;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("PredRealData-" + ip, JSON.stringify(result));

      client.expire("PredRealData-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllPredSNRData(res) {
  const response = await client.get("PredSNR");
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT a.ip, b.tag AS name, b.marca, b.tipo, b.rol AS subtipo, 'predict snr' AS status 
    FROM predicciones a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE tipo_prediccion LIKE '%SNR%'
    GROUP BY 1,2,3,4,5,6;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("PredSNR", JSON.stringify(result));

      client.expire("PredSNR", 300);

      res.json(result);
    }
  );
}

async function getPredTabSNRDataByIP(ip, res) {
  const response = await client.get("PredTableSNRData-" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT a.tipo_prediccion AS causa, DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, ROUND(a.value,2) AS snr, b.ip, 'predict snr' AS status 
    FROM predicciones a INNER JOIN inventario b ON a.ip = b.ip
    WHERE UPPER(tipo_prediccion) LIKE '%SNR%' AND a.ip = '${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY
    ORDER BY a.fecha DESC 
    LIMIT 20;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("PredTableSNRData-" + ip, JSON.stringify(result));

      client.expire("PredTableSNRData-" + ip, 300);

      res.json(result);
    }
  );
}

async function getPredSNRDataByIP(ip, res) {
  const response = await client.get("PredPredSNRData-" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT a.tipo_prediccion AS causa, DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, ROUND(value,2) AS snr 
    FROM predicciones a
    WHERE UPPER(tipo_prediccion)  LIKE '%SNR%' AND a.ip = '${ip}' AND fecha > NOW() - INTERVAL 30 DAY;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("PredPredSNRData-" + ip, JSON.stringify(result));

      client.expire("PredPredSNRData-" + ip, 300);

      res.json(result);
    }
  );
}

async function getRealSNRDataByIP(res, ip) {
  const response = await client.get("SNRRealDataByIp-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.snr
    FROM cambium_data a 
    WHERE ip = '${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("SNRRealDataByIp-" + ip, JSON.stringify(result));

      client.expire("SNRRealDataByIp-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllDataSNR(res) {
  const response = await client.get("AllSNRData");
  if (response) return res.json(JSON.parse(response));
}

/*****************************************
 ***************** SERVER ****************
 ****************************************/

async function getIPServer(res) {
  pool.query(
    `SELECT ip FROM inventario WHERE UPPER(tipo) = 'SERVIDOR'`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getAllServerData(res, ip) {
  const response = await client.get("ServerAlldata");
  if (response) return res.json(JSON.parse(response));

  let finalIp = ip.map((s) => `'${s}'`).join(", ");

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, a.info_snmp, b.tag AS name
    FROM servidor_data a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.ip IN (${finalIp}) AND a.fecha >= NOW() - INTERVAL 15 MINUTE
    GROUP BY 2,3,4 
    ORDER BY 1 DESC,2`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("ServerAlldata", JSON.stringify(result));

      client.expire("ServerAlldata", 300);

      res.json(result);
    }
  );
}

async function getAllServerGraphData(res, ip) {
  const response = await client.get("ServerGraphdata-" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.info_snmp, b.tag AS name
    FROM servidor_data a INNER JOIN inventario b ON a.ip = b.ip
    WHERE a.ip = '${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("ServerGraphdata-" + ip, JSON.stringify(result));

      client.expire("ServerGraphdata-" + ip, 300);

      res.json(result);
    }
  );
}

async function getVirMacServer(res, ip) {
  const response = await client.get("infoVirMac-" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, a.info_mv
    FROM servidor_data a
    WHERE a.ip = '${ip}' AND a.fecha IN (SELECT max(b.fecha) FROM servidor_data b)
    GROUP BY 1,2,3;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("infoVirMac-" + ip, JSON.stringify(result));

      client.expire("infoVirMac-" + ip, 100);
      res.json(result);
    }
  );
}

async function getVirMacByIP(res, ip, vm) {
  const response = await client.get("virtualMachine-" + ip + vm);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, CPUActual, MemoriaActual, DiscoActual, CPUFisico, MemoriaFisico, DiscoFisico
    FROM servidor_data a 
    WHERE a.ip = '${ip}' AND a.mv = '${vm}' AND a.fecha >= NOW() - INTERVAL 30 DAY;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("virtualMachine-" + ip + vm, JSON.stringify(result));

      client.expire("virtualMachine-" + ip + vm, 300);
      res.json(result);
    }
  );
}

async function getAlarmVirMac(res, ip, vm) {
  const response = await client.get("alarmrVirMac-" + ip + vm);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT host, nodo, status, causa, detalle, DATE_FORMAT(fecha, "%Y-%m-%d %H:%i:00") AS datetime
    FROM xsim_events WHERE host = '${ip}' AND causa LIKE '%${vm}%' AND fecha >= NOW() - INTERVAL 30 DAY - INTERVAL 2 HOUR ORDER BY fecha DESC;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("alarmrVirMac-" + ip + vm, JSON.stringify(result));

      client.expire("alarmrVirMac-" + ip + vm, 300);
      res.json(result);
    }
  );
}

/*****************************************
 ************** CLUSTERING ***************
 ****************************************/

async function getClustering(res) {
  pool.query(
    `SELECT DATE_FORMAT(Dia, '%Y-%m-%d %H:%i:00') AS fecha, html 
    FROM clustering 
    ORDER BY Dia DESC 
    LIMIT 4;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getClusteringData(res, fecha) {
  pool.query(
    `SELECT ip, DATE_FORMAT(fecha, '%Y-%m-%d %H:%i:00') AS fecha, latitud, longitud, latencia, fecha_db, cluster, label
    FROM clustering_data
    WHERE fecha >= '${fecha}'
    GROUP BY 1,2
    ORDER BY fecha DESC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getLast12HourClustering(res) {
  pool.query(
    `SELECT DISTINCT DATE_FORMAT(fecha, '%Y-%m-%d %H:%i:00') AS fecha 
    FROM clustering_data
    ORDER BY fecha DESC 
    LIMIT 12;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

/*****************************************
 *************** TOPOLOGY ****************
 ****************************************/

async function getAllOperabilityByIP(ip, res) {
  const response = await client.get("allOperability-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, c.rol AS subtipo,
    SUM(CASE WHEN a.latencia >= 0 AND a.latencia < 100  THEN 1 ELSE 0 END) AS ok,
    SUM(CASE WHEN a.latencia >= 100 AND a.latencia < 200 THEN 1 ELSE 0 END) AS alert,
    SUM(CASE WHEN a.latencia >= 200 AND a.latencia < 500 THEN 1 ELSE 0 END) AS alarm,
    SUM(CASE WHEN a.latencia >= 500 OR a.latencia < 0 THEN 1 ELSE 0 END) AS down
    FROM latencia a INNER JOIN inventario c ON a.ip = c.ip  
    WHERE a.fecha > NOW() - INTERVAL 30 DAY AND a.ip = '${ip}'
    GROUP BY a.fecha
    ORDER BY a.fecha DESC; `,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("allOperability" + ip, JSON.stringify(result));

      client.expire("allOperability" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllTopologyData(res) {
  const response = await client.get("topologystatus");
  if (response) return res.json(JSON.parse(response));
}

async function getGraphTopologyData(ip, type, res) {
  const response = await client.get(ip + "-" + type);
  if (response) return res.json(JSON.parse(response));

  const QUERY_TOPOLOGY = {
    latency: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.latencia AS kpi 
    FROM latencia a
    WHERE a.ip LIKE '${ip}' AND a.fecha >= NOW() - INTERVAL 30 DAY
    ORDER BY a.fecha ASC; `,

    cambium_data: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, 
    a.link_radio, 
    a.ifresults_metricas AS throughput,
    a.snr
    FROM cambium_data a
    WHERE a.ip LIKE '${ip}' AND a.fecha >= NOW() - INTERVAL 30 DAY 
    ORDER BY a.fecha ASC;`,

    linkradiohoriz: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.link_radio AS kpi 
    FROM cambium_data a
    WHERE a.ip LIKE '${ip}' AND a.fecha >= NOW() - INTERVAL 30 DAY 
    ORDER BY a.fecha ASC;`,

    linkradiovert: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.link_radio AS kpi 
    FROM cambium_data a 
    WHERE a.ip LIKE '${ip}' AND a.fecha >= NOW() - INTERVAL 30 DAY 
    ORDER BY fecha ASC;`,

    throughput: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ifresults_metricas AS kpi 
    FROM cambium_data a  
    WHERE a.ip LIKE '${ip}' AND a.fecha >= NOW() - INTERVAL 30 DAY  
    ORDER BY fecha ASC;`,

    wlan: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, wireless AS kpiObj 
    FROM rajant_data a
    WHERE a.ip LIKE '${ip}' AND a.fecha >= NOW() - INTERVAL 30 DAY
    ORDER BY a.fecha ASC;`,

    snr: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, snr
    FROM cambium_data a 
    WHERE a.ip LIKE '${ip}' AND a.fecha >= NOW() - INTERVAL 30 DAY  
    ORDER BY a.fecha ASC;`,
  };

  let queryFinal = QUERY_TOPOLOGY[type];

  pool.query(queryFinal, async (error, result) => {
    if (error) return console.log(error);

    await client.set(ip + "-" + type, JSON.stringify(result));

    client.expire(ip + "-" + type, 300);

    res.json(result);
  });
}

async function getTableTopologyData(ip, res) {
  const response = await client.get("TableTOPO" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT a.ip, a.latencia, 
    CASE 
      WHEN a.latencia >= 100 AND a.latencia < 200 THEN 'alert'
      WHEN a.latencia >= 200 AND a.latencia < 500 THEN 'alarm'
    END AS status,
    DATE_FORMAT(a.fecha, "%Y-%m-%d %H:%i:00") AS fecha 
    FROM latencia a 
    WHERE a.ip='${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY AND a.latencia >= 100 AND a.latencia <= 500
    ORDER BY a.fecha DESC LIMIT 6;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("TableTOPO" + ip, JSON.stringify(result));

      client.expire("TableTOPO" + ip, 300);

      res.json(result);
    }
  );
}

async function getstatusLogGraph(ip, res) {
  const response = await client.get("statuslog" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, "%Y-%m-%d %H:%i:00") AS fecha, a.ip, 
    CASE 
      WHEN a.latencia >= 0 AND a.latencia < 100 THEN 'ok'
      WHEN a.latencia >= 100 AND a.latencia < 200 THEN 'alert'
      WHEN a.latencia >= 200 AND a.latencia < 500 THEN 'alarm'
      ELSE 'down'
    END AS status
    FROM latencia a 
    WHERE a.ip = '${ip}' AND a.fecha >= NOW() - INTERVAL 30 DAY 
    ORDER BY a.fecha ASC`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("statuslog" + ip, JSON.stringify(result));

      client.expire("statuslog" + ip, 300);

      res.json(result);
    }
  );
}

async function getLatencyByEquip(ip, res) {
  const response = await client.get("LatencyEquip" + ip);
  if (response) return res.json(JSON.parse(response));

  let queryFinal = `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00')  AS fecha, a.latencia 
  FROM latencia a 
  WHERE a.ip LIKE '${ip}' AND a.fecha >= NOW() - INTERVAL 15 MINUTE
  ORDER BY a.fecha DESC`;

  pool.query(queryFinal, async (error, result) => {
    if (error) return console.log(error);

    await client.set("LatencyEquip" + ip, JSON.stringify(result));

    client.expire("LatencyEquip" + ip, 300);

    res.json(result);
  });
}

async function getLastGPSInfoRAJANT(res, ip) {
  const response = await client.get("lastGPSRAJANT-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT a.latitud, a.longitud 
    FROM ubicacion_gps a 
    WHERE a.ip = '${ip}' AND a.fecha > NOW() - INTERVAL 1 DAY
    ORDER BY a.fecha DESC 
    LIMIT 1;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("lastGPSRAJANT-" + ip, JSON.stringify(result));

      client.expire("lastGPSRAJANT-" + ip, 300);

      res.json(result);
    }
  );
}

async function getLastGPSInfoPMP(res, ip) {
  const response = await client.get("lastGPSPMP-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT ip, a.latitud, a.longitud, a.tag AS name, a.marca, a.tipo
    FROM ubicacion_gps a
    WHERE a.ip = '${ip}' 
    LIMIT 1;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("lastGPSPMP-" + ip, JSON.stringify(result));

      await client.expire("lastGPSPMP-" + ip, 300);

      res.json(result);
    }
  );
}

async function getSNMPDataByIP(res, ip) {
  pool.query(
    // `SELECT DATE_FORMAT(Datetime, '%Y-%m-%d %H:%i:00') as fecha, OID, CAST(Value AS SIGNED) AS 'Valor' FROM snmp_oid_list
    // WHERE ip = '${ip}' AND OID IN ('1.3.6.1.2.1.2.1.0', '1.3.6.1.2.1.2.2.1.1.1', '1.3.6.1.2.1.2.2.1.1.2', '1.3.6.1.2.1.4.1.0', '1.3.6.1.2.1.6.1.0', '1.3.6.1.2.1.4.1.0')`,
    `SELECT DATE_FORMAT(Datetime, '%Y-%m-%d %H:%i:00') as fecha, OID, CAST(Value AS SIGNED) AS 'Valor' FROM snmp_oid_list 
    WHERE ip = '${ip}' AND (
        OID LIKE '%1.3.6.1.4.1.4458.1000.1.5.9.1%' OR
        OID LIKE '%1.3.6.1.2.1.2.2.1.11%' OR
        OID LIKE '%1.3.6.1.2.1.2.2.1.14%' OR
        OID LIKE '%1.3.6.1.2.1.2.2.1.13%' OR
        OID LIKE '%1.3.6.1.2.1.31.1.1.1.6%' OR
        OID LIKE '%1.3.6.1.2.1.31.1.1.1.7%' OR
        OID LIKE '%1.3.6.1.2.1.2.2.1.17%' OR
        OID LIKE '%1.3.6.1.2.1.2.2.1.16%' OR
        OID LIKE '%1.3.6.1.2.1.2.2.1.20%' OR
        OID LIKE '%1.3.6.1.2.1.2.2.1.19%' OR
        OID LIKE '%1.3.6.1.2.1.31.1.1.1.10%' OR
        OID LIKE '%1.3.6.1.2.1.31.1.1.1.11%'
    ) AND Datetime >= NOW() - INTERVAL 30 DAY - INTERVAL 2 HOUR
    ORDER BY Datetime ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getSNMPUpDateDataByIP(res, ip) {
  let finalIP = ip;
  finalIP = "192.168.2.252";
  pool.query(
    // `SELECT DATE_FORMAT(Datetime, '%Y-%m-%d %H:%i:00') as fecha, OID, CAST(Value AS SIGNED) AS 'Valor' FROM snmp_oid_list
    // WHERE ip = '${ip}' AND OID IN ('1.3.6.1.2.1.1.3.0')`,
    `SELECT DATE_FORMAT(Datetime, '%Y-%m-%d %H:%i:00') as fecha, OID, CAST(Value AS SIGNED) AS 'Valor' FROM snmp_oid_list 
    WHERE ip = '${finalIP}' AND OID IN ('1.3.6.1.4.1.161.19.3.3.7.1.0')
    ORDER BY Datetime ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

// async function getStatusByIP(ip, res) {
//   const response = await client.get("statusBy-" + ip);
//   if (response) return res.json(JSON.parse(response));
//   pool.query(
//     `SELECT host_status AS status
//     FROM status_history
//     WHERE host_ip = '${ip}' AND resulttime >= NOW() - INTERVAL 15 MINUTE
//     ORDER BY resulttime DESC
//     LiMIT 1;`,
//     async (error, result) => {
//       if (error) return console.log(error);

//       await client.set("statusBy-" + ip, JSON.stringify(result));

//       // await client.expire("statusBy-" + ip, 300);

//       res.json(result);
//     }
//   );
// }

/*****************************************
 **************** REPORT *****************
 ****************************************/

async function getWorstOperability(res, fecini, fecfin, macType) {
  pool.query(
    `SELECT a.ip, c.tag AS name, c.tipo, 
    SUM(CASE WHEN a.latencia >= 0 AND a.latencia < 100  THEN 1 ELSE 0 END) AS ok,
    SUM(CASE WHEN a.latencia >= 100 AND a.latencia < 200 THEN 1 ELSE 0 END) AS alert,
    SUM(CASE WHEN a.latencia >= 200 AND a.latencia < 500 THEN 1 ELSE 0 END) AS alarm,
    SUM(CASE WHEN a.latencia >= 500 OR a.latencia < 0 THEN 1 ELSE 0 END) AS down
    FROM latencia a INNER JOIN inventario c ON a.ip = c.ip 
    WHERE UPPER(c.rol) = UPPER('${macType}') AND a.fecha BETWEEN '${fecini}' AND '${fecfin}' 
    GROUP BY a.ip, c.tag, c.tipo 
    ORDER BY ok DESC; `,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getWorstQualityLAP(res, fecini, fecfin, macType) {
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha , a.link_radio, a.avg_power AS avgpower, a.ip, b.tag AS name, b.tipo 
    FROM cambium_data a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE UPPER(b.rol) = UPPER('${macType}') AND a.fecha BETWEEN '${fecini}' AND '${fecfin}'   
    ORDER BY a.fecha DESC 
    LIMIT 100;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getWorstQualitySNR(res, fecini, fecfin, macType) {
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha , a.snr, a.avg_power AS avgpower, a.ip, b.tag AS name, b.tipo 
    FROM cambium_data a INNER JOIN inventario b ON a.ip = b.ip
    WHERE UPPER(b.rol) = UPPER('${macType}') AND a.fecha BETWEEN '${fecini}' AND '${fecfin}' ;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

// async function getWorstLatLng(res, fecini, fecfin) {
//   pool.query(
//     `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS datetime, gpsLat, gpsLong, IPv4
//     FROM instamesh
//     WHERE a.fecha BETWEEN '${fecini}' AND '${fecfin}';`,
//     async (error, result) => {
//       if (error) return console.log(error);
//       res.json(result);
//     }
//   );
// }

// async function getWorstLatency(res, fecini, fecfin) {
//   pool.query(
//     `SELECT DATE_FORMAT(fecha, '%Y-%m-%d %H:%i:00')  AS datetime, latency, ip
//     FROM LATENCY
//     WHERE fecha BETWEEN '${fecini}' AND '${fecfin}';`,
//     async (error, result) => {
//       if (error) return console.log(error);
//       res.json(result);
//     }
//   );
// }

async function getTENWorstLatency(res, fecini, fecfin, macType) {
  pool.query(
    `SELECT a.ip, b.tag AS name, b.tipo, AVG(a.latencia) AS latencia 
    FROM latencia a INNER JOIN inventario b ON a.ip = b.ip
    WHERE a.fecha BETWEEN '${fecini}' AND '${fecfin}' AND UPPER(b.rol) = UPPER('${macType}')
    GROUP BY a.ip
    order BY latencia DESC
    LIMIT 10;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getTopFiveLatency(res, fecini, fecfin, tipo, macType) {
  let rangeTime =
    tipo === "report"
      ? ` a.fecha BETWEEN '${fecini}' AND '${fecfin}' `
      : ` a.fecha >= NOW() - INTERVAL 12 HOUR`;
  pool.query(
    `SELECT a.ip 
    FROM latencia a INNER JOIN inventario b ON a.ip = b.ip
    WHERE UPPER(b.rol) = UPPER('${macType}') AND ${rangeTime}
    GROUP BY 1 
    ORDER BY a.latencia ASC 
    LIMIT 10;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getWorstLatLngByIp(res, fecini, fecfin, ip, tipo) {
  let finalIp = ip.map((s) => `'${s}'`).join(", ");
  let rangeTime =
    tipo === "report"
      ? ` a.fecha BETWEEN '${fecini}' AND '${fecfin}' `
      : ` a.fecha >= NOW() - INTERVAL 12 HOUR`;
  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.latitud, a.longitud, a.ip 
    FROM ubicacion_gps 
    WHERE ${rangeTime} AND a.ip IN (${finalIp})`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getWorstLatencyByIp(res, fecini, fecfin, ip, tipo) {
  let finalIp = ip.map((s) => `'${s}'`).join(", ");
  let rangeTime =
    tipo === "report"
      ? ` a.fecha BETWEEN '${fecini}' AND '${fecfin}' `
      : ` a.fecha >= NOW() - INTERVAL 12 HOUR `;
  pool.query(
    `SELECT DATE_FORMAT(fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.latencia, a.ip 
    FROM latencia a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.latencia > 0 AND b.rol = "Cliente" AND ${rangeTime} AND a.ip IN (${finalIp})
    ORDER BY a.latencia ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getAlarmData(res, ip, fecini, fecfin, alarm) {
  let finalIp = ip.map((s) => `'${s}'`).join(", ");
  let medida = alarm === "Poor" ? "ms" : "dB";
  let finalQuery =
    alarm !== "Poor"
      ? `SELECT
  DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha,
  a.causa,
  a.host,
  a.detalle,
  b.hostname,
  b.marca,
  b.tipo,
  '${medida}' AS medida, 
  d.gpslat AS latitud,
  d.gpslon AS longitud
  FROM
  xsim_events a
  INNER JOIN inventario b ON a.host = b.ip
  LEFT JOIN IFresults d ON a.host = d.ip AND DATE_FORMAT(d.resulttime, '%Y-%m-%d %H:%i:00') = DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00')
  WHERE
  a.host IN (${finalIp})
  AND a.fecha BETWEEN '${fecini}' AND '${fecfin}'
  AND a.causa LIKE '%${alarm}%'`
      : `SELECT
  DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha,
  a.causa,
  a.host,
  a.detalle,
  b.hostname,
  b.marca,
  b.tipo,
  '${medida}' AS medida, 
  a.gpsLat AS latitud,
  a.gpsLong AS longitud
  FROM
  alarmasgps a
  INNER JOIN inventario b ON a.host = b.ip
  WHERE
  a.host IN (${finalIp})
  AND a.fecha BETWEEN '${fecini}' AND '${fecfin}'
  AND a.causa LIKE '%${alarm}%'
  GROUP BY 1,2,3,4,5,6,7`;

  pool.query(finalQuery, async (error, result) => {
    if (error) return console.log(error);
    res.json(result);
  });
}

async function getDataHistory(res) {
  const response = await client.get("primaryDataHistory");
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT a.ip, a.tag AS name, a.rol AS subtipo 
    FROM inventario a`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("primaryDataHistory", JSON.stringify(result));

      client.expire("primaryDataHistory", 300);

      res.json(result);
    }
  );
}

/*****************************************
 *************** DBSTATUS ****************
 ****************************************/

async function getDataBaseStatus(res) {
  const response = await client.get("dataBaseStatus");
  if (response) return res.json(JSON.parse(response));
}

/*****************************************
 ************* CSV IVNENTORY *************
 ****************************************/

async function getDataInventory(res) {
  const response = await client.get("AllIPInventory");
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT a.ip, a.tag AS name, a.rol AS subtipo 
    FROM inventario a`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("AllIPInventory2", JSON.stringify(result));

      client.expire("AllIPInventory2", 300);

      res.json(result);
    }
  );
}

async function editDataInventory(data) {
  data.forEach((item) => {
    new Promise((resolve, reject) => {
      pool.query(
        `UPDATE inventario SET ? WHERE ip = ?`,
        [item, item.ip],
        (error, result) => {
          if (error) return reject(error);
          resolve(result);
        }
      );
    });
  });
}

async function editDataInventoryByName(data) {
  data.forEach((item) => {
    new Promise((resolve, reject) => {
      pool.query(
        `UPDATE inventario SET ? WHERE tag = ?`,
        [item, item.name],
        (error, result) => {
          if (error) return reject(error);
          resolve(result);
        }
      );
    });
  });
}

async function insertDataInventory(data) {
  data.forEach((item) => {
    return new Promise((resolve, reject) => {
      pool.query(`INSERT INTO inventario SET ?`, item, (error, result) => {
        if (error) return reject(error);
        resolve(result);
      });
    });
  });
}

/*****************************************
 ****************** LTE ******************
 ****************************************/

async function getIPLTE(res) {
  pool.query(
    `SELECT a.ip, a.tag AS name, a.tipo, a.rol AS subtipo, a.marca
    FROM inventario a 
    WHERE UPPER(a.tipo) = UPPER('LTE')`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getAllLTEData(res, ip) {
  const response = await client.get("LTEAlldata");
  if (response) return res.json(JSON.parse(response));

  let finalIp = ip.map((s) => `'${s}'`).join(", ");

  pool.query(
    // `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, a.sysDescr, a.ifDescr, a.ifOperStatus, a.ifMtu, a.ifSpeed, a.ifInUcastPkts, a.ifOutUcastPkts, a.sysUpTime, b.tag AS name
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, a.sistema, a.enlaces, a.estado, b.tag AS name
    FROM LTE_data a INNER JOIN inventario b ON a.ip = b.ip 
    WHERE a.ip IN (${finalIp}) AND a.fecha >= (SELECT MAX(c.fecha) FROM LTE_data c)
    GROUP BY 1,2,3,4,5,6;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("LTEAlldata", JSON.stringify(result));

      client.expire("LTEAlldata", 300);

      res.json(result);
    }
  );
}

async function getAllLTEDataGraph(res, ip) {
  const response = await client.get("LTEgraphdata-" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.enlaces, a.estado 
    FROM LTE_data a
    WHERE a.ip = '${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("LTEgraphdata-" + ip, JSON.stringify(result));

      client.expire("LTEgraphdata-" + ip, 300);

      res.json(result);
    }
  );
}

async function getLTE1Data(res, ip) {
  const response = await client.get("LTE1data-" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, name, type, APN, manufacturer, model, 
    IMEI, IMSI, registrationstatus, networkmode, rssi, rsrp, rsrq, currentoperator, lac, currentcellid, enbid, sectorid, 
    txbytes, rxbytes, lastlinkdowntime, lastlinkuptime, linkdowns, 
    lat, lon 
    FROM LTE_data a WHERE a.ip = '${ip}' AND a.fecha > NOW() - INTERVAL 1 HOUR
    ORDER BY a.fecha DESC 
    LIMIT 1;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("LTE1data-" + ip, JSON.stringify(result));

      client.expire("LTE1data-" + ip, 300);

      res.json(result);
    }
  );
}

async function getSNMPModemALLDataByIP(res, ip) {
  const response = await client.get("snmpModemALLdata-" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, rssi, rsrp, rsrq, txbytes, rxbytes
    FROM LTE_data a 
    WHERE a.ip = '${ip}' AND a.fecha > NOW() - INTERVAL 30 DAY;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("LTE1ALLdata-" + ip, JSON.stringify(result));

      client.expire("LTE1ALLdata-" + ip, 300);

      res.json(result);
    }
  );
}

/*****************************************
 ************** PAGE STATUS **************
 ****************************************/

async function getPageStatus(res) {
  pool.query(
    `SELECT 1 AS status 
    FROM inventario LIMIT 1`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

/*****************************************
 ************** CONTROL DB ***************
 ****************************************/

async function deleteDataInDB(table, time) {
  let querys = {
    cambium_data: `DELETE FROM cambium_data WHERE fecha < '${time}';`,
    eventos: `DELETE FROM eventos WHERE fecha < '${time}';`,
    latencia: `DELETE FROM latencia WHERE fecha < '${time}';`,
    LTE_data: `DELETE FROM LTE_data WHERE fecha < '${time}';`,
    predicciones: `DELETE FROM predicciones WHERE fecha < '${time}';`,
    rajant_data: `DELETE FROM rajant_data WHERE fecha < '${time}';`,
    sensores: `DELETE FROM sensores WHERE fecha < '${time}';`,
    servidor_data: `DELETE FROM servidor_data WHERE fecha < '${time}';`,
    ubicacion_gps: `DELETE FROM ubicacion_gps WHERE fecha < '${time}';`,
  };
  let selectedQuery = querys[table];
  return new Promise((resolve, reject) => {
    pool.query(`${selectedQuery}`, (error, result) => {
      if (error) return reject(error);
      resolve(result);
    });
  });
}

/*****************************************
 ************** CONTROL OID **************
 ****************************************/

async function getAllOIDs(res) {
  pool.query(
    `SELECT OID, CodeName FROM snmp_oid_list`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function allDataServer(res, ip) {
  const response = await client.get("ServerDataAdditional-" + ip);
  if (response) return res.json(JSON.parse(response));

  pool.query(
    `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, procesos, cpu, memoria, mvs, sensores, uptime 
    FROM servidor_data 
    WHERE a.ip = '${ip}' AND fecha >= NOW() - INTERVAL 1 HOUR
    ORDER BY a.fecha DESC 
    LIMIT 1;`,
    async (error, result) => {
      if (error) return console.log(error);

      await client.set("ServerDataAdditional-" + ip, JSON.stringify(result));
      client.expire("ServerDataAdditional-" + ip, 300);

      res.json(result);
    }
  );
}

// async function getNetworkData() {
//   return new Promise((resolve, reject) => {
//     pool.query(
//       `SELECT * FROM inventario WHERE tipo IN ('PMP','PMP-AP');`,
//       (error, result) => {
//         if (error) return reject(error);
//         resolve(result);
//       }
//     );
//   });
// }

async function getStatusHistoryByIP(ip, res) {
  const response = await client.get("StatusHistory-" + ip);
  if (response) return res.json(JSON.parse(response));

  // FROM latencia a INNER JOIN inventario c ON a.ip = c.ip
  // WHERE a.fecha > NOW() - INTERVAL 30 DAY
  // GROUP BY 1,2
  // ORDER BY ok DESC
  pool.query(
    `SELECT a.ip, c.tag AS name, c.tipo, c.tipo, c.rol AS subtipo
    SUM(CASE WHEN a.latencia >= 0 AND a.latencia < 100  THEN 1 ELSE 0 END) AS ok, 
    SUM(CASE WHEN a.latencia >= 100 AND a.latencia < 200 THEN 1 ELSE 0 END) AS alert, 
    SUM(CASE WHEN a.latencia >= 200 AND a.latencia < 500 THEN 1 ELSE 0 END) AS alarm, 
    SUM(CASE WHEN a.latencia >= 500 OR a.latencia < 0 THEN 1 ELSE 0 END) AS down 
    FROM latencia a INNER JOIN inventario c ON a.ip = c.ip 
    WHERE a.fecha > NOW() - INTERVAL 30 DAY AND a.ip = '${ip}' 
    GROUP BY a.ip, c.tag, c.tipo  
    ORDER BY ok DESC`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("StatusHistory-" + ip, JSON.stringify(result));

      client.expire("StatusHistory-" + ip, 300);

      res.json(result);
    }
  );
}

async function getAllSNRDataByIP(res, ip) {
  const response = await client.get("AllSNRDataByIp-" + ip);
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(a.fecha,'%Y-%m-%d %H:%i:00') AS fecha, a.ip, c.latitud, c.longitud, a.snr, b.tag AS name, b.tipo 
    FROM cambium_data a 
    INNER JOIN inventario b ON a.ip = b.ip 
    INNER JOIN ubicacion_gps c ON a.ip = c.ip 
    WHERE a.fecha > Now() - INTERVAL 180 MINUTE AND a.ip = '${ip}' AND DATE_FORMAT(a.fecha,'%Y-%m-%d %H:%i:00') = DATE_FORMAT(c.fecha,'%Y-%m-%d %H:%i:00');`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("AllSNRDataByIp-" + ip, JSON.stringify(result));

      client.expire("AllSNRDataByIp-" + ip, 5 * 60);

      res.json(result);
    }
  );
}

async function getLastConectionHaultruck(res) {
  const response = await client.get("getLastConectionHaultruck");
  if (response) return res.json(JSON.parse(response));
}

async function getCountLastConectionHaultruck(res) {
  const response = await client.get("getCountLastConectionHaultruck");
  if (response) return res.json(JSON.parse(response));
}

async function getAllDataGestor(res) {
  // const response = await client.get('AllDataGestor');
  // if (response) return res.json(JSON.parse(response));
  let items = [];
  let options = {
    mode: "text",
    pythonOptions: ["-u"],
    scriptPath: "newScripts",
    args: ["192.168.2.60"],
  };

  await PythonShell.run("LTE_get_config.py", options).then((messages) => {
    items = messages;
  });

  return res.json(items);

  // await client.set('AllDataGestor', JSON.stringify(items));
}

async function getAllDataIPS2(res) {
  const response = await client.get("allDataIPS2");
  if (response) return res.json(JSON.parse(response));
}

async function getMaxDatesLTE(res) {
  // WHERE a.fecha = (SELECT MAX(fecha) FROM LTE_data )
  pool.query(
    `SELECT DATE_FORMAT(b.fecha,'%Y-%m-%d %H:%i:00') AS fecha FROM LTE_data b GROUP BY 1 ORDER BY b.fecha DESC LIMIT 2;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getLastLTE(res, dates) {
  let finalDates = dates.map((s) => `'${s}'`).join(", ");
  // WHERE a.fecha = (SELECT MAX(fecha) FROM LTE_data )
  pool.query(
    `SELECT DATE_FORMAT(a.fecha,'%Y-%m-%d %H:%i:00') AS fecha, a.ip, a.sistema, a.enlaces, a.estado 
    FROM LTE_data a 
    WHERE DATE_FORMAT(a.fecha,'%Y-%m-%d %H:%i:00') IN (${finalDates})
    GROUP BY 1,2,3,4,5
    ORDER BY a.ip ASC, a.fecha ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      res.json(result);
    }
  );
}

async function getLast30DaysLTE(res) {
  const response = await client.get("getLast30DaysLTE");
  if (response) return res.json(JSON.parse(response));
  pool.query(
    `SELECT DATE_FORMAT(a.fecha,'%Y-%m-%d %H:%i:00') AS fecha, a.ip, a.sistema, a.enlaces, a.estado 
    FROM LTE_data a 
    WHERE a.fecha > Now() - INTERVAL 30 DAY
    ORDER BY a.ip ASC;`,
    async (error, result) => {
      if (error) return console.log(error);
      await client.set("getLast30DaysLTE", JSON.stringify(result));

      client.expire("getLast30DaysLTE", 5 * 60);

      res.json(result);
    }
  );
}

module.exports = {
  getAllOperability,
  getAllOperabilityByIP,
  getAllOperabilityLastDay,
  // getStatusByIP,
  getLast12HourClustering,
  getPositionHaulTrucks,
  getAllHaulTrucks,
  getAllHaulTrucksDrive,
  getKPIDashboard,
  insertDataInventory,
  getDataHistory,
  getIPServer,
  getAllIPS,
  getLastGPSInfoPMP,
  getLastGPSInfoRAJANT,
  getDataBaseStatus,
  getDataInventory,
  // getCoverage,
  getStatusHistoryByIP,
  getAllWirelessData,
  getLTE1Data,
  getAllWirelessDataByIP,
  getAllWiredDataByIP,
  getAllTempDataByIP,
  getAllCostDataByIP,
  getAllTopologyData,
  getAllData,
  addData,
  editData,
  deleteData,
  getAllLTEData,
  getIPLTE,
  getAllServerData,
  getCostWiredpeers,
  getCostWirelesspeers,
  getClustering,
  getClusteringData,
  allDataServer,
  getAllWiredData,
  getAllTempData,
  getAllCostData,
  getAllCostJRData,
  getAllServerGraphData,
  getPredTableRXLVLData,
  getGraphTopologyData,
  getTableTopologyData,
  getSNMPDataByIP,
  getSNMPUpDateDataByIP,
  getAllDataSNR,
  getPredSNRDataByIP,
  getAllPredSNRData,
  getRealSNRDataByIP,
  getPredTabSNRDataByIP,
  getAllDataKPI,
  getAllSNRDataByIP,
  getAllRXLVLRealDataByIP,
  getAllRXLVLPredDataByIP,
  getAllLTEDataGraph,
  // getWorstLatency,
  getAlarmData,
  getAlarmToDashBoard,
  getAlarmRecurrentToDashBoard,
  // getNetworkData,
  getUserLogin,
  getstatusLogGraph,
  getAllLatLngPMPSM,
  getAllCostJRDataByIP,
  getPageStatus,
  getWorstOperability,
  getWorstQualityLAP,
  getWorstQualitySNR,
  // getWorstLatLng,
  getAllLatLngPMPAP,
  getAllPolylines,
  getAllLatLngRAJANT,
  getAllLatLngANY,
  getAllLatLngGPSTEST,
  getLatencyByEquip,
  editDataInventory,
  getTopFiveLatency,
  getTENWorstLatency,
  getWorstLatLngByIp,
  getWorstLatencyByIp,
  editDataInventoryByName,
  getSubTypeInventory,
  getTypeInventory,
  getMarkInventory,
  getSNMPInventory,
  getVirMacServer,
  getVirMacByIP,
  getAlarmVirMac,
  getAllLatency,
  getAllPredictRXLVLData,
  getSNMPModemALLDataByIP,
  deleteDataInDB,
  getAllOIDs,
  getPositionDrives,
  getPositionDrivesRajant,
  getLastConectionHaultruck,
  getCountLastConectionHaultruck,
  getAllDataGestor,
  getAllDataIPS2,
  getLastLTE,
  getLast30DaysLTE,
  getMaxDatesLTE,
};
