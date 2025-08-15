const SELECT_QUERY = {
  latency: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') as fecha, a.ip, b.tag AS name, b.rol AS subtipo, a.latencia, b.tipo 
    FROM inventario b INNER JOIN latencia a ON b.ip = a.ip  
    WHERE (latencia > 200 OR latencia < 0) AND a.fecha > NOW() - INTERVAL 1 MINUTE
    ORDER BY fecha DESC;`,

  quality_lap: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha , a.snr, a.link_radio, a.avg_power AS avgpower, a.ip, b.tag AS name, b.tipo 
    FROM inventario b INNER JOIN cambium_data a ON a.ip=b.ip 
    WHERE a.fecha > NOW() - INTERVAL 1 MINUTE 
    ORDER BY a.fecha desc;`,

  quality_snr: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha , a.snr, a.link_radio, a.avg_power AS avgpower, a.ip, b.tag AS name, b.tipo 
    FROM inventario b INNER JOIN cambium_data a ON a.ip=b.ip 
    WHERE fecha > NOW() - INTERVAL 1 MINUTE 
    ORDER BY a.fecha DESC;`,

  pack_inst: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, b.tag AS name, b.tipo, a.instamesh 
    FROM inventario b INNER JOIN rajant_data a ON a.ip = b.ip 
    WHERE a.fecha > NOW() - INTERVAL 1 MINUTE  
    ORDER BY a.fecha DESC;`,

  temp_inst: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, b.tag AS name, b.tipo, a.valores
    FROM inventario b INNER JOIN sensores a ON a.ip = b.ip 
    WHERE a.fecha > NOW() - INTERVAL 1 MINUTE
    ORDER BY  a.fecha desc;`,

  wire_inst: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, b.tag AS name, b.tipo, a.config, a.wireless
    FROM inventario b INNER JOIN rajant_data a ON a.ip = b.ip 
    WHERE a.fecha > NOW() - INTERVAL 1 MINUTE
    ORDER BY a.fecha DESC;`,

  operability: `SELECT a.ip, c.tag AS name, c.tipo, c.rol AS subtipo,
  SUM(CASE WHEN a.latencia >= 0 AND a.latencia < 100  THEN 1 ELSE 0 END) AS ok, 
  SUM(CASE WHEN a.latencia >= 100 AND a.latencia < 200 THEN 1 ELSE 0 END) AS alert, 
  SUM(CASE WHEN a.latencia >= 200 AND a.latencia < 500 THEN 1 ELSE 0 END) AS alarm, 
  SUM(CASE WHEN a.latencia >= 500 OR a.latencia < 0 THEN 1 ELSE 0 END) AS down 
  FROM latencia a INNER JOIN inventario c ON a.ip = c.ip 
  WHERE a.fecha > NOW() - INTERVAL 1 DAY
  GROUP BY 1,2 
  ORDER BY ok DESC`,

  kpisnr: `SELECT DISTINCT(a.ip),MAX(DATE_FORMAT(a.fecha, "%Y-%m-%d %H:%i:00")) AS fecha , a.snr, b.tag AS name, b.tipo 
  FROM inventario b INNER JOIN cambium_data a ON a.ip=b.ip 
  WHERE fecha > NOW() - INTERVAL 1 MINUTE 
  GROUP BY a.ip;`,
};

const KPI_QUERYS_LAST_TIME = {
  latency: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') as fecha, a.ip, b.tag AS name, b.tipo, b.rol AS subtipo, a.latencia, b.tipo 
    FROM inventario b INNER JOIN latencia a ON b.ip = a.ip  
    WHERE a.fecha = (SELECT MAX(fecha) FROM latencia)
    ORDER BY latencia DESC;`,

  quality_lap: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha , a.snr, a.link_radio, a.avg_power AS avgpower, a.ip, b.tag AS name, b.tipo, b.rol AS subtipo
    FROM inventario b INNER JOIN cambium_data a ON a.ip=b.ip 
    WHERE a.fecha = (SELECT MAX(fecha) FROM cambium_data)
    ORDER BY a.fecha DESC`,

  temp_inst: `SELECT DATE_FORMAT(a.fecha, '%Y-%m-%d %H:%i:00') AS fecha, a.ip, b.tag AS name, b.tipo, b.rol AS subtipo, a.valores 
    FROM inventario b INNER JOIN sensores a ON a.ip = b.ip 
    WHERE a.fecha = (SELECT MAX(c.fecha) FROM sensores c)
    GROUP BY 1,2,3,4,5`,

  operability: `SELECT a.ip, c.tag AS name, c.tipo, c.rol AS subtipo,
  SUM(CASE WHEN a.latencia >= 0 AND a.latencia < 100  THEN 1 ELSE 0 END) AS ok, 
  SUM(CASE WHEN a.latencia >= 100 AND a.latencia < 200 THEN 1 ELSE 0 END) AS alert, 
  SUM(CASE WHEN a.latencia >= 200 AND a.latencia < 500 THEN 1 ELSE 0 END) AS alarm, 
  SUM(CASE WHEN a.latencia >= 500 OR a.latencia < 0 THEN 1 ELSE 0 END) AS down 
  FROM latencia a INNER JOIN inventario c ON a.ip = c.ip 
  WHERE a.fecha > NOW() - INTERVAL 30 DAY
  GROUP BY 1,2 
  ORDER BY ok DESC`,
};

module.exports = {
  SELECT_QUERY,
  KPI_QUERYS_LAST_TIME,
};
