// ++============================================++
// ||                   A U X                    ||
// ++============================================++

function normalize(text) {
    return String(text).trim().toLowerCase().replaceAll(' ', '_');
}

function clearUrl(text){
    return text.replace('url("', '').replace('")', '');
}

function linkToText(elem) {
    return `${elem.innerText} (${elem.href})`
}

function getBgImageUrl(elem){
    return clearUrl(elem.style.backgroundImage)
}

function cleanInnerText(elem, reg, rep='') {
    if (reg == null) {
        return normalize(elem.innerText);
    } else {
        return elem.innerText.trim().replaceAll(reg, rep)
    }
}

function printJson(data) {
    console.log(data);
    console.log(
        JSON.stringify(data)
            .replaceAll("\\'", "'")
            .replaceAll("'ill", ' will')
            .replaceAll("'", '\\\\\\"')
            .replaceAll('\\"', '\\\\\\"')
        );
}

// ++============================================++
// ||               C L A S S E S                ||
// ++============================================++

class Metadata {
    constructor() {
        // Basic metadata info
        this.title = null
        this.tags = []
        this.url = null
        this.description = null
        this.difficulty = null
        this.status = null
        this.logo = null
        this.authors = []
        // Custom args
        this.os = null
        this.points = null
        this.rating = null
        this.targets = []
        this.release_date = null
        this.related_academy_modules = null
    }
}

class _Resource {
    constructor(rtype) {
        this.__type__ = 'htb.' + rtype;
        this.metadata = new Metadata();
    }
}

class _Module extends _Resource {
    static Section(type=null, title=null) {
        return {
            __type__: type,
            title: title
        }
    };

    constructor(rtype) {
        super(rtype);
        this.sections = [];
    }
}

class _Path extends _Resource {
    constructor(rtype) {
        super(rtype);
        this.sections = 0;
        this.modules = [];
    }
}

class _Exercise extends _Resource {
    static Task(text=null, answer=null, points=null) {
        return {
            text: text,
            answer: answer,
            points: points
        }
    }

    constructor(rtype) {
        super(rtype);
        this.tasks = [];
    }
}

// ++============================================++
// ||          D A T A   C L A S S E S           ||
// ++============================================++

class HtbModule extends _Module {
	static TIER_COST = {
		'0': 10,
		'I': 50,
		'II': 100,
		'III': 500,
		'IV': 1000
	}
	static COST_TIER = {
		10: '0',
		50: 'I',
		100: 'II',
		500: 'III',
		1000: 'IV'
	}
	static POINTS_TIER = {
	    10: '0',
	    10: 'I',
	    20: 'II',
        100: 'III',
        200: 'IV'
	}

	constructor(){
	    super('mod');
		this._tier = null;
		this.duration = null;
		this.summary = null;
	}
}

class HtbPath extends _Path {
    constructor(rtype=null){
        if (rtype == null) {
            super(document.URL.endsWith('jobrole')?'jpt':'spt'); // skill-path, job-role-path
        } else {
            super(rtype)
        }
        // this._progress = 0.0;
        this.cost = 0;
        this.duration = null
    }
}

class HtbExercise extends _Exercise {
    constructor(rtype) {
        super(rtype);
    }
}

// ++============================================++
// ||      A C A D E M Y   P A R S E R S         ||
// ++============================================++

function getModule(){
	if(!document.URL.startsWith('https://academy.hackthebox.com/module/details')){
		console.error('Invalid URL. Go to an specific module to parse it.')
		return null;
	}
	const res = new HtbModule();

	const infoCard = document.querySelector('h5').parentElement.parentElement.parentElement;
	const basicInfoText = infoCard.children[0].innerText.split('\n');

	res.metadata.url = document.URL;
	res.metadata.title = basicInfoText[0].trim();
	res.metadata.logo = document.querySelector('img.card-img.img-fluid').src;
	res.metadata.difficulty = basicInfoText[2];
	res.metadata.tags.push(basicInfoText[3]);   // category
	// If first badge different from 'Tier', remove it from the list
	if(!basicInfoText[1].startsWith('Tier ')){
		res.metadata.tags.push(basicInfoText.splice(1, 1)[0]);
	}

	res.metadata.description = infoCard.children[1].innerText;
	res.metadata.rating = infoCard.children[2].querySelector('input').value;
	res.metadata.authors = cleanInnerText(infoCard.children[3], /Created by |\nCo-Authors:/g).split(', ');
    // Get section title and type
    res.sections = Array.from(document.querySelector('h3').parentElement.nextElementSibling.querySelectorAll('li')).map(item => {
        return _Module.Section(
				item.children[0].getAttribute('data-title'), // type
				item.innerText  // title
			);
    });

    // Custom attr
	res._tier = basicInfoText[1].split(' ')[1];
	res.duration = basicInfoText[4];
	res.summary = cleanInnerText(document.querySelector('h3').parentElement, 'Module Summary\n\n')

	printJson(res)
	return res;
}

function getPath(){
    const ALL_PATHS = Array.from(document.querySelector('div.row.paths-content > div').children).map(item => {
        let _innerText = item.innerText.split('\n\n')
        let res = new HtbPath()

        res.metadata.title = _innerText[0];
        res.metadata.difficulty = normalize(_innerText[1].split(' ')[0]);
        res.metadata.points = Number(_innerText[1].split(' ')[3]);
        res.metadata.description = _innerText[3];
        res.metadata.logo = document.querySelector('img.card-img.img-fluid').src;
        res.metadata.url = document.URL;
        res.metadata.authors.push('HTB');
        res.sections = Array.from(item.querySelectorAll('div.card-body')[1].querySelectorAll('a')).map(item => {
             const _innerText = cleanInnerText(
                    item.parentElement.nextElementSibling,
                    /( |\n)+/g,
                    '-'
                ).split('-');
            let mod = new HtbModule();
            mod.metadata.title = item.innerText.trim();
            mod.metadata.url = item.href;
            mod.metadata.difficulty = normalize(_innerText[0]);
            mod.sections = Number(_innerText[1].trim().split(' ')[0]);
            mod.metadata.points = Number(_innerText[3].trim()); // 3 is reward, reward => tier
            mod.tier = HtbModule.POINTS_TIER[mod.metadata.points];
            return mod
        });

        // Custom attributes
        res._progress = Number(_innerText[5].split('%')[0]) / 100;
        res.cost = Number(_innerText[2].split(': ')[1]);
        res.duration = `${_innerText[1].split(' ')[5]} ${_innerText[1].split(' ')[6]}`;
        return res
    });
    printJson(ALL_PATHS);
    return ALL_PATHS;
}

// ++============================================++
// ||           L A B   P A R S E R S            ||
// ++============================================++

function getStartingPoint(){
    const _activeElem = document.querySelector('div.v-item--active');

    const res = new HtbExercise('stp');

    res.metadata.url = document.URL;
    res.metadata.authors.push('HTB');
    res.metadata.title = _activeElem.querySelectorAll('button p')[0].innerText;
    res.metadata.difficulty = cleanInnerText(_activeElem.querySelectorAll('button p')[1]);
    res.metadata.points = 0;
    res.metadata.logo = getBgImageUrl(_activeElem.querySelector('div[style^="background-image: url("]'));
    res.metadata.os = _activeElem.querySelector('div.avatar-icon > i').classList.contains('icon-linux')?'linux':'windows';
    try {
        res.metadata.status = cleanInnerText(_activeElem.querySelectorAll('button p')[2]);
    } catch(error) { // No third index => no 'pwned' tag => in progress
        res.metadata.status = 'in_progress';
    }
    // Pop 'Official writeup' and 'Video walkthrough' tags
    res.metadata.tags = cleanInnerText(
            _activeElem.children[1].children[0].children[0],
            'Tags\n'
        ).split('\n').filter(x => !x.startsWith('Official') || x.startsWith('Video'));
    res.tasks = Array.from(document.querySelectorAll('div.v-card__text'))
        .filter(x => x.innerText.startsWith('TASK'))
        .map(item => {
            let taskText = item.innerText.replace('TASK ', '').split('\n\n');
            // get Task text, answer and points
            return _Exercise.Task(...taskText.slice(1, 2).concat(taskText.slice(3)))
        }
    );
    printJson(res)
    return res;
}

function getMachine(){
    const _headerElem = document.querySelector('#machineProfileHeader');
    let _headerText = _headerElem.innerText.replace(' · ', '\n').split('\n')
    const res = new HtbExercise('mch')

    if (_headerText[0].includes('Retired')){
        res.metadata.tags.push(_headerText.splice(0, 1)[0])
    }  // Pop this tag, is not useful
    if (_headerText[0].includes('is offline')){_headerText.splice(0, 1)}  // Pop this tag, is not useful

    res.metadata.url = document.URL.replace('/information', '');
    res.metadata.authors.push(linkToText(document.querySelector('a[href^="/users/"]')));
    res.metadata.logo = getBgImageUrl(_headerElem.querySelector('div.v-image__image.v-image__image--cover'));
    res.metadata.title = _headerText.splice(0, 1)[0];
    res.metadata.os = _headerText.splice(0, 1)[0];
    res.metadata.difficulty = _headerText.splice(0, 1)[0];
    res.metadata.points = Number(_headerText.splice(0, 2)[0]);
    res.metadata.rating = Number(_headerText.splice(0, 2)[0]);

    try {  // Get task list. Try to obtain 'Guided mode', else get 'Adventure mode' (default)
        taskCards = Array.from(document.querySelectorAll('div.machineTasks div.v-expansion-panels')[1].children);
    } catch(error) {
        taskCards = Array.from(document.querySelectorAll('div.machineTasks div.v-expansion-panels')[0].children);
    } finally {
        res.tasks = taskCards.map(item => {
            if(item.innerText.trim().startsWith('Task')){
                try{ answer=item.querySelector('input').value; } catch(error){ answer = null;}
                try {
                    text = cleanInnerText(item.querySelector('span > p'), /Submit (User|Root) Flag /g)
                } catch(error) {
                    text = item.innerText.trim();
                }
                return _Exercise.Task(text, answer);
            } else {
                return _Exercise.Task(...cleanInnerText(item, /Submit (User|Root) Flag /g).split('\n\n'))
            }
        });
    }

    function getMachineDetails(res){
        if(document.querySelectorAll('div.tab')[1].classList.contains('v-tab--active')){
            const _elem = document.querySelector('#MachineProfileInfoTab > div > div');
            for(let i = 0; i < _elem.childElementCount; i++){
                if(_elem.children[i].innerText === ''){
                    continue;
                }
                let detailsText = _elem.children[i].innerText.split('\n');
                let firstLine = detailsText.splice(0, 1)[0];
                let description = detailsText.splice(0, 1)[0];
                switch(firstLine){
                    case `About ${res.metadata.title}`:
                        res.metadata.description = detailsText.join('\n');
                        break;
                    case "Related Academy Modules":
                        let aux = [];
                        // TODO: Auto-link to modules
                        detailsText.pop();
                        for (let j = 0; j < detailsText.length; j+=2){
                            aux.push(`${detailsText[j]} (${detailsText[j+1]})`);
                        }
                        res.metadata[normalize(firstLine)] = aux;
                        break;
                    case 'Machine Bloods':
                        i = _elem.childElementCount; // stop the loop
                        break;
                    default:
                        res.metadata[normalize(firstLine)] = detailsText;
                }
            }
            res.metadata.release_date = document.querySelector('i.icon-calendar-2').parentElement.innerText.trim();
            // total_pwns = document.querySelector('div.row.totalPwns').innerText.split('\n');
            // for(let j = total_pwns.length - 1; j <= 0; j-=2){
            //      res.info[total_pwns[j]] = Number(total_pwns[j-1]);
            // }
        }
        printJson(res);
        return res;
    }
    document.querySelectorAll('div.tab')[1].click(); // Click 'Machine info' button to load the corresponding HTML
    setTimeout(getMachineDetails, 2000, res);
}

function getChallenge(){
    let _profileElem = document.querySelector('#machineProfile');
    let _detailsText = document.querySelector('div.machine-tags').nextElementSibling.innerText.split('\n')
    const res = new HtbExercise('chl');

    res.metadata.logo = 'https://app.hackthebox.com/images/logos/htb_ic2.svg';
    res.metadata.os = 'docker';
    res.metadata.url = document.URL;
    res.metadata.description = document.querySelector('div.machine-tags > p').innerText.trim();
    res.metadata.title = _profileElem.children[0].innerText.split('\n')[0];
    res.metadata.difficulty = normalize(_profileElem.children[0].innerText.split('\n')[1]);
    res.metadata.points = Number(cleanInnerText(document.querySelector('div.pt-7'), 'POINTS'));
    res.metadata.status = _detailsText.includes('CHALLENGE COMPLETED')?'completed':'in_progress';
    res.metadata.rating = Number(_detailsText[0])
    res.metadata.tags.push(_detailsText[4]);
    res.metadata.release_date = _detailsText[6] + ' ago';
    res.metadata.authors.push(_detailsText[8]);

    printJson(res);
    return res;
}

function getSherlock(){
    let _headerElem = document.querySelector('div.sherlock-profile-header')
    let _headerText = _headerElem.innerText.split('\n');
    let _playInfoElem = document.querySelector('div.v-tabs-items div.borderEbonyClay').children;
    const res = new HtbExercise('shr');

    res.metadata.os = 'any';
    res.metadata.url = document.URL.replace('/play', '');
    res.metadata.authors.push(linkToText(document.querySelector('a[href^="/users/"]')));
    res.metadata.logo = getBgImageUrl(_headerElem.querySelectorAll('div[style^="background-image:"]')[1]);
    res.metadata.title = _headerText.splice(0, 1)[0];
    res.metadata.difficulty = normalize(_headerText.splice(0, 1)[0]);
    res.metadata.rating = Number(_headerText.splice(0, 1)[0].trim())
    res.metadata.targets.push(_playInfoElem[1].innerText.split('\n')[0]);
    if(document.querySelector('div.pt-7') != null) {
        res.metadata.points = Number(cleanInnerText(document.querySelector('div.pt-7'), 'POINTS'));
    }
    if(_headerText[0].startsWith('Retired')){
        res.metadata.tags.push(_headerText.splice(0, 1)[0]);
    }
    res.tasks = Array.from(document.querySelectorAll('div.task-item')).map(item => {
        return _Exercise.Task(
            item.querySelector('span.markdown-section').innerText,
            item.querySelector('input').value === ''?item.querySelector('input').placeholder:item.querySelector('input').value
        );
    });

    // Get detailed info
    function getSherlockInfo(res){
        // If 'Info' tab disabled cannot parse its data
        if(!document.querySelectorAll('a.v-tab')[1].classList.contains('v-tab--disabled')){
            res.metmachineadata.release_date = document.querySelector('i.icon-calendar-2').parentElement.innerText.trim();
            // res.metadata.solves = document.querySelector('i.icon-userflag').parentElement.innerText.trim();

            const _infoElem = document.querySelector('div[state^="retired"] > div > div');
            for(let i = 0; i < _infoElem.childElementCount; i++){
                if(_infoElem.children[i].innerText === ''){
                    continue;
                }
                let sectionContent = _infoElem.children[i].innerText.split('\n');
                let firstLine = sectionContent.splice(0, 1)[0];
                let description = sectionContent.splice(0, 1)[0];
                switch(firstLine){
                    case `About ${res.metadata.title}`:
                        res.metadata.description = sectionContent.join('\n');
                        break;
                    case "Related Academy Modules":
                        let aux = [];
                        // TODO: Auto-link to modules
                        sectionContent.pop();
                        for (let j = 0; j < sectionContent.length; j+=2){
                            aux.push(`${sectionContent[j]} (${sectionContent[j+1]})`);
                        }
                        res.metadata[normalize(firstLine)] = aux;
                        break;
                    default:
                        res.metadata[normalize(firstLine)] = sectionContent;
                }
            }
        }
        printJson(res);
        return res;
    }
    document.querySelectorAll('a.v-tab')[1].click();  // Click 'Sherlock info' button to load the corresponding HTML
    setTimeout(getSherlockInfo, 2000, res);
}

function getTrack(){
    let _infoElem = document.querySelector('div.cursorPointer.back-arrow + div');
    let _infoText = _infoElem.innerText.split('\n');
    const res = new HtbPath('trk');

    res.metadata.url = document.URL;
    res.metadata.logo = _infoElem.querySelector('img').src;
    res.metadata.description = document.querySelector('p.htb-label + p').innerText.trim();
    res.metadata.authors.push(document.querySelector('p.htb-label + div img').src);
    // Get progress !! Deduced from number of completed tasks
    //res.metadata.status = Number(document.querySelector('div.highcharts-container span span').innerText) / 100;
    res.metadata.title = _infoText[0];
    res.metadata.difficulty = normalize(_infoText[1]);
    if(_infoText[2] != ''){
        res.metadata.tags.push(_infoText[2]);
    }
    // get track items (machines and/or challenges)
    res.sections = Array.from(document.querySelector('div[xs="12"] > div').children).map(item => {
        if(item.querySelector('i.icon-linux') != null){ // Linux icon, is a machine
            _ = new HtbExercise('mch')
            _.metadata.os = 'linux'
        } else if(item.querySelector('i.icon-windows') != null) { // Windows icon, is a machine
            _ = new HtbExercise('mch')
            _.metadata.os = 'windows'
        } else { // If no OS, is a sherlock
            _ = new HtbExercise('shr')
        }
        try {
            _.metadata.logo = getBgImageUrl(item.querySelector('div[style^="background-image:"]'));
        } catch(error){ // If no logo, is a challenge
             _ = new HtbExercise('chl')
        }
        _.metadata.title = item.innerText.split('\n')[0];
        _.metadata.difficulty = normalize(item.innerText.split('\n')[1]);
        return _
    });
    printJson(res);
    return res;
}

function getProLab(){
    let _overviewElems = document.querySelector('span.font-size54').parentElement.nextElementSibling.querySelectorAll('span')
    const res = new HtbExercise('lab');

    res.metadata.url = document.URL;
    res.metadata.title = document.querySelector('span.font-size54').innerText;
    res.metadata.logo = document.querySelector('img[src^="/images/icons/ic-prolabs"]').src;
    res.metadata.tags.push(`${_overviewElems[0].innerText} (${_overviewElems[1].innerText})`);
    res.metadata.difficulty = normalize(_overviewElems[3].innerText); // Get difficulty

    function getLabDetails(res){
        res.entry_point = document.querySelector('span.pt-2.font-size16.fontSemiBold.noWrap.color-green').innerText;

        // Get target machines
        res.targets = Array.from(document.querySelectorAll('div.machinecard')).map(item => {
            let _ = new HtbExercise('mch');
            _.metadata.title = item.innerText;
            _.metadata.logo = getBgImageUrl(item.querySelector('div[style^="background-image:"]'));
            if(item.querySelector('i.icon-windows') != null){
                _.metadata.os = 'windows';
            } else if(item.querySelector('i.icon-linux') != null) {
                _.metadata.os = 'linux';
            }
            return _
        });
        let _taskElems = Array.from(document.querySelector('div.col div.animated.fadeIn').children);
        if(_taskElems[0].querySelector('p.flag-intro') != null){  // 'Introduction' section
            let _ = Array.from(_taskElems[0].querySelector('p.flag-intro').children);
            res.metadata.title = _.splice(0, 1)[0].innerText;
            res.metadata.authors.push(_.splice(0, 1)[0].innerText);
            res.metadata.description = _.map(e=> e.innerText).join('\n');
            _taskElems.splice(0, 1)
        }
        res.tasks = _taskElems.map(item => {
            return _Exercise.Task(
                text=item.innerText.split('\n')[0],
                answer=null,
                points=item.innerText.split('\n')[1].split(' ')[0]
            )
        });
        printJson(res);
        return res;
    }
    document.querySelectorAll('div[role="tab"]')[0].click(); // Click 'Lab' button to load corresponding HTML
    setTimeout(getLabDetails, 2000, res);
}

function getFortress() {
    const res = new HtbExercise('ftr');

    res.metadata.difficulty = 'real_scenario';
    res.metadata.url = document.URL;
    res.metadata.title = document.querySelector('p.htb-text.pr-12').previousElementSibling.innerText.split(' ').pop();
    res.metadata.authors.push(res.metadata.title); // Author and Name have the same value
    res.metadata.logo = document.querySelector('div.fortressBanner img').src;
    res.metadata.description = document.querySelector('p.htb-text.pr-12').innerText;
    res.metadata.points = Number(document.querySelector('div.fortressBanner').innerText.split('\n\n')[2].split(' ')[0]);

    // Get tasks
    let _taskElems = Array.from(document.querySelector('div.col div[class="animated fadeIn"]').children)
    if(_taskElems[0].querySelector('p.flag-intro') != null) { // Intro section
        res.metadata.description = _taskElems[0].querySelector('p.flag-intro').innerText;
        _taskElems.splice(0, 1)
    }
    res.tasks = _taskElems.map(item => {
        return _Exercise.Task(
                text=item.innerText.split('\n')[0],
                answer=null,
                points=Number(item.innerText.split('\n')[1].replace(' POINTS', ''))
        )
    });
    // Custom attributes
    // res.completions = Number(document.querySelector('div.fortressBanner').innerText.split('\n\n')[0])
    res.entry_point = document.querySelector('span.pt-2.font-size16.fontSemiBold.noWrap.color-green').innerText;

    printJson(res);
    return res;
}

function getBattleground(){
    const res = new HtbExercise('btg');
    res.metadata.url = document.URL;
    // TODO: implement
    console.warn("NOT IMPLEMENTED: getBattleground()");
    printJson(res);
    return res
}

// ++============================================++
// ||                  M A I N                   ||
// ++============================================++


function help(){
	console.log([
		'HTB toolkit, by @uRHL',
		'- help()             -> Prints this message and exits',
		'\nCLASSES',
		'- Task               -> Task (text, answer, points)',
		'- Section            -> Section (type, title)',
		'- HtbModule          -> Module details (title, duration, tier, ...)',
		'- HtbPath            -> Collections of modules',
		'- HtbExercise        -> HTB exercise (machine, challenge, sherlock, ...)',
		'\nACADEMY PARSERS',
		"- getModule()        -> Get details from module's details page",
		'- getPath()          -> Return a list of HtbPath instances',
		'\nLAB PARSERS',
		'- getStartingPoint() -> Parses the currently focused Starting Point machine',
		'- getMachine()       -> Parses a regular HTB Machine',
		'- getChallenge()     -> Parses a challenge',
		'- getSherlock()      -> Parses a Sherlock',
		'- getTrack()         -> Parses a Track',
		'- getProLab()        -> Parses a Pro-Lab',
		'- getFortress()      -> Parses a Fortress (advanced lab)',
	].join('\n'));
}

function main(){
    if(document.URL.startsWith('https://app.hackthebox.com/battlegrounds/')){
        getBattleground();
    } else if(document.URL.startsWith('https://app.hackthebox.com/fortresses/')){
        getFortress();
    } else if(document.URL.startsWith('https://app.hackthebox.com/prolabs/')){
        getProLab();
    } else if(document.URL.startsWith('https://app.hackthebox.com/tracks/')){
        getTrack();
    } else if(document.URL.startsWith('https://app.hackthebox.com/sherlocks/')){
        getSherlock();
    } else if(document.URL.startsWith('https://app.hackthebox.com/challenges/')){
        getChallenge();
    } else if(document.URL.startsWith('https://app.hackthebox.com/machines/')){
        getMachine();
    } else if(document.URL.startsWith('https://app.hackthebox.com/starting-point')){
        getStartingPoint();
    } else if(document.URL.startsWith('https://academy.hackthebox.com/module/details/')){
        getModule();
    } else if(document.URL.startsWith('https://academy.hackthebox.com/modules')){
        listModules();
    } else if(document.URL.startsWith('https://academy.hackthebox.com/paths')){
        getPath();
    } else {
        console.warn('Invalid URL. No data to extract');
        help();
    }
}

main();