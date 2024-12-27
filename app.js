

const queryString = window.location.search;
const params = new URLSearchParams(queryString);
if (params.has("preza")) {
    window.location.replace("https://docs.google.com/presentation/d/13lIQqcAnXGaNrzAMM508xcA-iOYoq2-HcWiJWThj6rg/view");
    //window.location.href = "https://docs.google.com/presentation/d/13lIQqcAnXGaNrzAMM508xcA-iOYoq2-HcWiJWThj6rg/view";
}

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


const eduquals = {
  "B": "Бакалавриат",
  "M": "Магистратура",
  "A": "Аспирантура",
  "S": "Специалитет",
  "1": "Базовое высшее образование",
  "2": "Cпециализированное высшее образование",
  "_": "Неизвестно" 
}

const eduforms = { 
    "Z": "Заочная",
    "O": "Очная",
    "V": "Очно-заочная"
}

//console.log("sql.js initialized");

const QUERY_DISCIPLINE_NAMES = `
SELECT 
    dn.id AS id,
    dn.name AS name
FROM discipline_names dn
WHERE LOWER(dn.name) LIKE ?;
`;
const QUERY_PROGRAMS = `
SELECT
    p.id AS id,
    p.uid AS uid,
    pn.name AS name,
    pc.code AS code
FROM disciplines d
JOIN plans pl ON d.plan_id = pl.id
JOIN programs p ON p.id = pl.program_id
JOIN program_names pn ON pn.id = p.name_id
JOIN program_codes pc ON pc.id = p.code_id
WHERE d.name_id = ?
GROUP BY p.uid;
`;


const QUERY = `
SELECT 
    p.id AS id,
    pn.name AS name,
    pc.code AS code,
    u.uid AS university_code
FROM programs p
JOIN program_codes pc ON pc.id = p.code_id
JOIN program_names pn ON pn.id = p.name_id
JOIN universities u ON u.id = p.university_id
WHERE p.id = ?;
`;

const QUERY_PLANS = `
SELECT 
    pl.year AS year,
    pl.id AS id,
    pl.pdf_url AS pdf_url
FROM plans pl
WHERE pl.program_id = ?;
`;

const QUERY1 = `
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
FROM discipline_names dn
JOIN disciplines d ON dn.id = d.name_id
JOIN discipline_codes dc ON dc.id = d.code_id 
JOIN plans pl ON d.plan_id = pl.id
JOIN programs p ON p.id = pl.program_id
JOIN program_codes pc ON pc.id = p.code_id
JOIN program_names pn ON pn.id = p.name_id
JOIN universities u ON u.id = p.university_id
WHERE LOWER(dn.name) LIKE ?;
`;

function handleChange() {
    const inputValue = document.getElementById('search-bar').value;
    //console.log('Input changed to:', inputValue);
  
    parse_discipline_names(inputValue);
    return;
    
}

function parse_discipline_names(inputValue) {

    const container = document.getElementById("search-results-discipline-names");
    container.innerHTML = '';

    if (inputValue.length === 0) {
        return;
    }
    if (inputValue.length < 2) {
        return;
    }
    const stmt = db.prepare(QUERY_DISCIPLINE_NAMES);
    stmt.bind([`%${inputValue}%`]);

    const results = [];
    var k = 0;
    while (stmt.step()) {
        const result = stmt.getAsObject();
        //console.log(result);
        const listItem = document.createElement('li');
        listItem.textContent = result.name; 
        //listItem.setAttribute('data-id', result.id);
        listItem.classList.add('result-item');
        listItem.setAttribute('dn-id', result.id);
        listItem.addEventListener('click', () => {
            const dn_id = listItem.getAttribute('dn-id');
            const dn_name = listItem.textContent;
            handle_discipline_click(dn_id,dn_name);
        });
        container.appendChild(listItem);
        k++;
    }
    //console.log(k);
}

function handle_discipline_click(dn_id,dn_name) {
    document.getElementById("d-title").textContent = dn_name;
    const container = document.getElementById("search-results-discipline-programs");
    container.innerHTML = '';
    const stmt = db.prepare(QUERY_PROGRAMS);
    stmt.bind([dn_id]);
    const results = [];
    var k = 0;
    while (stmt.step()) {
        const result = stmt.getAsObject();
        console.log(result);
        const listItem = document.createElement('li');
        listItem.textContent = result.name; 
        //listItem.setAttribute('data-id', result.id);
        listItem.classList.add('result-item');
        listItem.setAttribute('p-id', result.id);
        listItem.addEventListener('click', () => {
            const p_id = listItem.getAttribute('p-id');
            handle_program_click(p_id);
        });
        container.appendChild(listItem);
        k++;
    }
    open_page_discipline();

}

function handle_program_click(p_id) {

    const container = document.getElementById("search-results-program-plans");
    container.innerHTML = '';
   
    const stmt1 = db.prepare(QUERY);
    stmt1.bind([p_id]);
    stmt1.step();
    const p = stmt1.getAsObject();
    document.getElementById("p-title").textContent = p.name;
    console.log(p)

    const stmt = db.prepare(QUERY_PLANS);
    stmt.bind([p_id]);

    const results = [];
    var k = 0;
    while (stmt.step()) {
        const result = stmt.getAsObject();
        //console.log(result);
        const list1Item = document.createElement('li');
        const listItem = document.createElement('a');
        listItem.textContent = result.year.toString(); 
        //listItem.setAttribute('data-id', result.id);
        list1Item.classList.add('result-item');
        list1Item.setAttribute('pl-id', result.id);
        listItem.setAttribute('href', result.pdf_url);

        //listItem.addEventListener('click', () => {
        //    const p_id = listItem.getAttribute('p-id');
        //    handle_program_click(p_id);
        //});
        list1Item.appendChild(listItem);
        container.appendChild(list1Item);
        k++;
    }
    
    console.log(p_id);
    open_page_program()
}

function open_page_search() {
    document.getElementById('page-program').style.display = "none"; 
    document.getElementById('page-discipline').style.display = "none"; 
    document.getElementById('page-search').style.display = "block"; 
    //document.getElementById('search-bar').addEventListener('change', handleChange);
    document.getElementById('search-bar').addEventListener('input', handleChange);

    handleChange()
}


function open_page_discipline() {
    document.getElementById('page-search').style.display = "none"; 
    document.getElementById('page-program').style.display = "none"; 
  document.getElementById('page-discipline').style.display = "block"; 
}

function open_page_program() {
    document.getElementById('page-search').style.display = "none"; 
    document.getElementById('page-discipline').style.display = "none"; 
    document.getElementById('page-program').style.display = "block"; 
    const program = params.get('program')
}

if (params.has("program")) {
    open_page_program()
} else {
    open_page_search()
}



//async function find_by_discipline() {}
