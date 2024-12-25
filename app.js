
const initSqlJs = window.initSqlJs;
const config = {
  locateFile: file => `https://sql.js.org/dist/${file}`
};
const sqlPromise = initSqlJs(config);
const dataPromise = fetch("./data/db.sqlite3").then(res => res.arrayBuffer());

const [SQL, buf] = await Promise.all([sqlPromise, dataPromise])
const db = new SQL.Database(new Uint8Array(buf));

const icons = {
  "misis": "https://misis.ru/f/src/images/favicon-32x32.png"
}

console.log("sql.js initialized");

const QUERY = `
SELECT 
    d.id AS discipline_id,
    d.semester AS discipline_semester,
    d.hours AS discipline_hours,
    dn.name AS discipline_name,
    dc.code AS discipline_code,
    pl.year AS plan_year,
    pl.id AS plan_id,
    p.id AS program_id,
    pn.name AS program_name,
    pc.code AS program_code,
    u.uid AS university_code
FROM 
    discipline_names dn
JOIN 
    disciplines d ON dn.id = d.name_id
JOIN
    discipline_codes dc ON dc.id = d.code_id 
JOIN 
    plans pl ON d.plan_id = pl.id
JOIN
    programs p ON p.id = pl.program_id
JOIN
    program_codes pc ON pc.id = p.code_id
JOIN
    program_names pn ON pn.id = p.name_id
JOIN
    universities u ON u.id = p.university_id
WHERE 
    LOWER(dn.name) LIKE ?;`;

function handleChange() {
    const inputValue = document.getElementById('search-bar').value;
    console.log('Input changed to:', inputValue);

    if (inputValue.length === 0) {
        return;
    }
    const stmt = db.prepare(QUERY);
    stmt.bind([`%${inputValue}%`]);

    const results = [];
    var k = 0;
    while (stmt.step()) {
        console.log(stmt.getAsObject());
        k = k+1;
    }
  console.log(k);



}

document.getElementById('search-bar').addEventListener('change', handleChange);

//async function find_by_discipline() {}
