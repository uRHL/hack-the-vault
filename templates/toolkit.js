// ++============================================++
// ||                   A U X                    ||
// ++============================================++

function normalize(text) {
    return String(text).toLowerCase().replaceAll(' ', '_');
}

function clearUrl(text){
    return text.replace('url("', '').replace('")', '');
}

function getBackgroundImageUrl(elem){
    return clearUrl(elem.style.backgroundImage);
}

function printJson(data) {
    console.log(data);
    console.log(JSON.stringify(data).replaceAll("'ill", ' will').replaceAll("'", '\\"'));
}

// ++============================================++
// ||               C L A S S E S                ||
// ++============================================++

class Task {
    constructor(number, text, answer='ANSWER', points=0) {
        this.number = number===null?1:Number(number);
        this.text = text===null?`Task ${this.number}`:text;
        this.answer = [null, undefined].includes(answer)?'ANSWER':answer;
        this.points = Number(points);
    }
}

class HtbModule {
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
		this._type = 'mod';
		this.info = {
			url: null,
			name: null,
		    description: null,
			difficulty: null,
			status: null,
			logo: null,
			os: null,
			authors: [],
			tags: [],
			points: null
		};
		this.about = {
		    rating: null
		};
		this.tier = null;
		this.duration = null;
		this.summary = null;
		this.sections = [];
	}
}

class HtbPath {
    constructor(pType=null){
        this._progress = 0.0;
        this._type = ['spt', 'jpt'].includes(pType)?pType:null; // skill-path, job-role-path
        this.info = {
            name: null,
            difficulty: null,
            points: 0,
            description: null,
            authors: []
        }
        this.cost = 0;
        this.duration = null,
        this.sections = [];
        this.modules = [];
    }
}

class HtbMachine {
    constructor(mtype) {
        this._type = mtype;
        this.info = {
            url: null,
            name: null,
            difficulty: null,
            description: null,
            status: null,
            logo: null,
            os: null,
            tags: [],
            points: 0,
            authors: []
        };
        // description, release_date, related academy modules
        this.about = { //m, ch, sh
            release_date: null, //m, ch, sh
            rating: null, //ch, sh
            related_academy_modules: null, //m, sh
            targets: [], //sh, pl
        };
        this.tasks = []; //sp, m, ch, sh, tk, pl, ft
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
	const mod = new HtbModule();

	const infoCard = document.querySelector('h5').parentElement.parentElement.parentElement;
	const basicInfoText = infoCard.children[0].innerText.split('\n');
	mod.info.url = document.URL;
	mod.info.name = basicInfoText[0].trim();
	mod.info.logo = document.querySelector('img.card-img.img-fluid').src;
	// If first badge different from 'Tier', remove it from the list
	if(!basicInfoText[1].startsWith('Tier ')){
		mod.info.family = basicInfoText.splice(1, 1)[0];
	}
	mod.tier = basicInfoText[1].split(' ')[1];
	mod.info.difficulty = basicInfoText[2];
	mod.info.tags.push(basicInfoText[3]); // category
	mod.duration = basicInfoText[4];
	mod.info.description = infoCard.children[1].innerText;
	mod.about.rating = infoCard.children[2].querySelector('input').value;
	mod.info.authors = infoCard.children[3].innerText
		.replace('Created by ', '')
		.replace('\nCo-Authors:', ',')
		.split(', ');

	mod.summary = document.querySelector('h3').parentElement.innerText.replace('Module Summary\n\n', '');
	// Get section title and type
	Array.from(
		document.querySelector('h3').parentElement.nextElementSibling.querySelectorAll('li')
		).forEach(item => {
			mod.sections.push({
				'name': item.innerText,
				'_type': item.children[0].getAttribute('data-title')
			});
		}
	)
	printJson(mod)
	return mod;
}

function listModules(){
	if(document.URL != 'https://academy.hackthebox.com/modules'){
		console.error('Invalid URL. Go to academy > modules')
		return null;
	}

	const ALL_MODS = [];
	Array.from(document.querySelector('div.row.module-list').querySelectorAll('div.card')).forEach(elem => {
		const mod = new HtbModule();
		const badgeCards = Array.from(elem.querySelectorAll('span.badge'));
		// If first badge different from 'Tier', remove it from the list
		if(!badgeCards[0].innerText.startsWith('Tier ')){
			mod.info.family = badgeCards.shift().innerText;
		}
		mod.info.url = elem.querySelector('a').href;
		mod.info.name = elem.querySelector('h4').innerText.trim();
		// Always same order: Tier, Difficulty, Category, #sections, reward, duration
		mod.tier = badgeCards[0].innerText.split(' ')[1];
		mod.info.difficulty = badgeCards[1].innerText;
		mod.info.tags.append(badgeCards[2].innerText);
		mod.sections = Number(badgeCards[3].innerText.split(' ')[0]);
		mod.duration = badgeCards[5].innerText;
		ALL_MODS.push(mod);
	});
    printJson(ALL_MODS)
	return ALL_MODS;
}

function listPaths(){
    const _type = document.URL.endsWith('jobrole')?'jpt':'spt';
    const ALL_PATHS = [];
    Array.from(document.querySelector('div.row.paths-content > div').children).forEach(item => {
        let split = item.innerText.split('\n\n')
        let path = new HtbPath(_type)
        path.info.name = split[0];
        path.info.difficulty = normalize(split[1].split(' ')[0]);
        path.sections = Number(split[1].split(' ')[1]);
        path.info.points = Number(split[1].split(' ')[3]);
        path.duration = `${split[1].split(' ')[5]} ${split[1].split(' ')[6]}`;
        path.cost = Number(split[2].split(': ')[1]);
        path.info.description = split[3];
        path.info.logo = document.querySelector('img.card-img.img-fluid').src;
        path.info.url = document.URL;
        path.info.authors.push('HTB');
        path._progress = Number(split[5].split('%')[0]) / 100;

        // Get modules then link to modules
        Array.from(item.querySelectorAll('div.card-body')[1].querySelectorAll('a')).forEach(item => {
            const detailsCard = item.parentElement.nextElementSibling.innerText.trim().replaceAll(/( |\n)+/g, '-').split('-');
            console.warn(detailsCard);
            let mod = new HtbModule();
            mod.info.name = item.innerText.trim();
            mod.info.url = item.href;
            mod.info.difficulty = normalize(detailsCard[0].trim());
            mod.sections = Number(detailsCard[1].trim().split(' ')[0]);
            mod.info.points = Number(detailsCard[3].trim()); // 3 is reward, reward => tier
            mod.tier = HtbModule.POINTS_TIER[mod.info.points];
            console.warn(mod)
            path.modules.push(mod)
        });
        ALL_PATHS.push(path);
    });
    printJson(ALL_PATHS);
    return ALL_PATHS;
}

// ++============================================++
// ||           L A B   P A R S E R S            ||
// ++============================================++

function getStartingPoint(){
    const activeCard = document.querySelector('div.v-item--active');
    const machine = new HtbMachine('stp');
    machine.info.url = document.URL;
    machine.info.authors.push('HTB');
    machine.info.name = activeCard.querySelectorAll('button p')[0].innerText;
    machine.info.difficulty = normalize(activeCard.querySelectorAll('button p')[1].innerText);
    machine.info.points = 0;

    try {
        machine.info.status = normalize(activeCard.querySelectorAll('button p')[2].innerText);
    } catch(error) { // No third index => no 'pwned' tag => in progress
        machine.info.status = 'in_progress';
    }

    machine.info.logo = getBackgroundImageUrl(activeCard.querySelector('div[style^="background-image: url("]'));
    machine.info.os = activeCard.querySelector('div.avatar-icon > i').classList.contains('icon-linux')?'linux':'windows';

    // Pop 'Official writeup' and 'Video walkthrough' tags
    machine.info.tags = activeCard.children[1].children[0].children[0].innerText.replace('Tags\n', '').split('\n').filter(x => !x.startsWith('Official') || x.startsWith('Video'));

    Array.from(document.querySelectorAll('div.v-card__text')).forEach(item => {
        if(item.innerText.startsWith('TASK')){
            let taskText = item.innerText.replace('TASK ', '').split('\n\n');
            let task = taskText.length > 2?new Task(taskText[0], taskText[1], taskText[3]):new Task(taskText[0], taskText[1]);
            machine.tasks.push(task);
        }
    });
    printJson(machine)
    return machine;
}

function getMachine(){
    const machine = new HtbMachine('mch')
    machine.info.url = document.URL.replace('/information', '');
    machine.info.authors.push(`${document.querySelector('a[href^="/users/"]').innerText} (${document.querySelector('a[href^="/users/"]').href})`);
    const headerCard = document.querySelector('#machineProfileHeader');
    machine.info.logo = getBackgroundImageUrl(headerCard.querySelector('div.v-image__image.v-image__image--cover'));

    let headerText = headerCard.innerText.replace(' · ', '\n').split('\n')
    machine.info.difficulty = headerText.pop();
    machine.info.os = headerText.pop();
    machine.info.name = headerText.pop();
    machine.info.tags = headerText.filter(item => !['Submit Machine Matrix', 'Submit Machine Review'].includes(item));
    machine.info.points = Number(document.querySelectorAll('span.fontMedium.color-white')[0].innerText);
    machine.about.rating = Number(document.querySelectorAll('span.fontMedium.color-white')[1].innerText)


    // Get task list. Try to obtain 'Guided mode', else get 'Adventure mode' (default)
    let taskCards = null;
    try {
        taskCards = Array.from(document.querySelectorAll('div.machineTasks div.v-expansion-panels')[1].children);
    } catch(error) {
        taskCards = Array.from(document.querySelectorAll('div.machineTasks div.v-expansion-panels')[0].children);
    }
    for(let i = 0; i < taskCards.length; i++) {
        let task = null;
        if(taskCards[i].innerText.trim().startsWith('Task')){
            try{
                answer=taskCards[i].querySelector('input').value;
            } catch(error){
                answer = null;
            }
            try {
                text = taskCards[i].querySelector('span > p').innerText.replace(/Submit (User|Root) Flag /g, '').trim()
            } catch(error) {
                text = taskCards[i].innerText.trim();
            }
            task = new Task(i+1, text, answer);
        } else {
            task = new Task(
                i+1,
                ...taskCards[i].innerText.replace(/Submit (User|Root) Flag /g, '').trim().split('\n\n')
            )
        }
        machine.tasks.push(task);
    }

    function getMachineDetails(machine){
        if(document.querySelectorAll('div.tab')[1].classList.contains('v-tab--active')){
            const infoCard = document.querySelector('#MachineProfileInfoTab > div > div');
            for(let i = 0; i < infoCard.childElementCount; i++){
                if(infoCard.children[i].innerText === ''){
                    continue;
                }
                let detailsText = infoCard.children[i].innerText.split('\n');
                let firstLine = detailsText.splice(0, 1)[0];
                let description = detailsText.splice(0, 1)[0];
                switch(firstLine){
                    case `About ${machine.info.name}`:
                        machine.info.description = detailsText.join('\n');
                        break;
                    case "Related Academy Modules":
                        let aux = [];
                        // TODO: Auto-link to modules
                        detailsText.pop();
                        for (let j = 0; j < detailsText.length; j+=2){
                            aux.push(`${detailsText[j]} (${detailsText[j+1]})`);
                        }
                        machine.about[normalize(firstLine)] = aux;
                        break;
                    case 'Machine Bloods':
                        i = infoCard.childElementCount; // stop the loop
                        break;
                    default:
                        machine.about[normalize(firstLine)] = detailsText;
                }
            }
            machine.about.release_date = document.querySelector('i.icon-calendar-2').parentElement.innerText.trim();
            // total_pwns = document.querySelector('div.row.totalPwns').innerText.split('\n');
            // for(let j = total_pwns.length - 1; j <= 0; j-=2){
            //      machine.info[total_pwns[j]] = Number(total_pwns[j-1]);
            // }
        }
        printJson(machine);
        return machine;
    }
    document.querySelectorAll('div.tab')[1].click(); // Click 'Machine info' button to load the corresponding HTML
    setTimeout(getMachineDetails, 2000, machine);
}

function getChallenge(){
    const machine = new HtbMachine('chl');
    machine.info.url = document.URL;
    machine.info.os = 'docker';
    machine.info.description = document.querySelector('div.machine-tags > p').innerText.trim();

    const profile_card = document.querySelector('#machineProfile');
    machine.info.name = profile_card.children[0].innerText.split('\n')[0];
    machine.info.difficulty = normalize(profile_card.children[0].innerText.split('\n')[1]);
    machine.info.points = Number(document.querySelector('div.pt-7').innerText.replace('POINTS', ''));
    machine.info.logo = 'https://app.hackthebox.com/images/logos/htb_ic2.svg';

    let detailsText = document.querySelector('div.machine-tags').nextElementSibling.innerText.split('\n')
    machine.info.status = detailsText.includes('CHALLENGE COMPLETED')?'completed':'in_progress';
    for (let i = 0; i < detailsText.length; i+=2){  // Only interested in the first 5 attributes
        switch(i){
            case 0:
                machine.about.rating = Number(detailsText[i])
                break;
            case 4:
                machine.info.tags.push(detailsText[i]);
                break;
            case 6:
                machine.about.release_date = detailsText[i] + ' ago';
                break;
            case 8:
                machine.info.authors.push(detailsText[i]);
                break;
        }
    }
    printJson(machine);
    return machine;
}

function getSherlock(){
    const sherlock = new HtbMachine('shr');
    sherlock.info.url = document.URL.replace('/play', '');
    sherlock.info.os = 'any';
    sherlock.info.authors .push(`${document.querySelector('a[href^="/users/"]').innerText} (${document.querySelector('a[href^="/users/"]').href})`);
    const headerCard = document.querySelector('div.sherlock-profile-header')
    sherlock.info.logo = getBackgroundImageUrl(headerCard.querySelectorAll('div[style^="background-image:"]')[1]);
    if(document.querySelector('div.pt-7') != null) {
        sherlock.info.points = Number(document.querySelector('div.pt-7').innerText.replace('POINTS', ''));
    }

    const playInfoCards = document.querySelector('div.v-tabs-items div.borderEbonyClay').children;
    let headerText = headerCard.innerText.split('\n');

    if(headerText[0].startsWith('Retired')){
        sherlock.info.tags.push(headerText.splice(0, 1)[0]);
    }
    sherlock.info.name = headerText.splice(0, 1)[0];
    sherlock.info.difficulty = normalize(headerText.splice(0, 1)[0]);
    sherlock.about.rating = Number(headerText.splice(0, 1)[0].trim())
    sherlock.about.targets.push(playInfoCards[1].innerText.split('\n')[0]);

    // Get tasks
    let taskCards = Array.from(document.querySelectorAll('div.task-item'));
    for(let i = 0; i < taskCards.length; i++){
        sherlock.tasks.push(new Task(
            i+1,
            taskCards[i].querySelector('span.markdown-section').innerText,
            taskCards[i].querySelector('input').value === ''?taskCards[i].querySelector('input').placeholder:taskCards[i].querySelector('input').value
        ));
    }

    // Get detailed info
    function getSherlockInfo(sherlock){
        // If 'Info' tab disabled cannot parse its data
        if(!document.querySelectorAll('a.v-tab')[1].classList.contains('v-tab--disabled')){
            sherlock.about.release_date = document.querySelector('i.icon-calendar-2').parentElement.innerText.trim();
            // machine.info.solves = document.querySelector('i.icon-userflag').parentElement.innerText.trim();

            const infoCard = document.querySelector('div[state^="retired"] > div > div');
            for(let i = 0; i < infoCard.childElementCount; i++){
                if(infoCard.children[i].innerText === ''){
                    continue;
                }
                let sectionContent = infoCard.children[i].innerText.split('\n');
                let firstLine = sectionContent.splice(0, 1)[0];
                let description = sectionContent.splice(0, 1)[0];
                switch(firstLine){
                    case `About ${sherlock.about.name}`:
                        sherlock.info.description = sectionContent.join('\n');
                        break;
                    case "Related Academy Modules":
                        let aux = [];
                        // TODO: Auto-link to modules
                        sectionContent.pop();
                        for (let j = 0; j < sectionContent.length; j+=2){
                            aux.push(`${sectionContent[j]} (${sectionContent[j+1]})`);
                        }
                        sherlock.about[normalize(firstLine)] = aux;
                        break;
                    default:
                        sherlock.about[normalize(firstLine)] = sectionContent;
                }
            }
        }
        printJson(sherlock);
        return sherlock;
    }
    document.querySelectorAll('a.v-tab')[1].click();  // Click 'Sherlock info' button to load the corresponding HTML
    setTimeout(getSherlockInfo, 2000, sherlock);
}

function getTrack(){
    const track = new HtbMachine('trk');
    track.info.url = document.URL;

    const infoCard = document.querySelector('div.cursorPointer.back-arrow + div');
    track.info.logo = infoCard.querySelector('img').src;
    track.info.description = document.querySelector('p.htb-label + p').innerText.trim();
    track.info.authors.push(document.querySelector('p.htb-label + div img').src);
    // Get progress !! Deduced from number of completed tasks
    //track.info.status = Number(document.querySelector('div.highcharts-container span span').innerText) / 100;

    let infoText = infoCard.innerText.split('\n');
    track.info.name = infoText[0];
    track.info.difficulty = normalize(infoText[1]);
    if(infoText[2] != ''){
        track.info.tags.push(infoText[2]);
    }
    // get track items (machines and/or challenges)
    Array.from(document.querySelector('div[xs="12"] > div').children).forEach(item => {
        let trackItem = new HtbMachine('mch');
        trackItem.info.name = item.innerText.split('\n')[0];
        trackItem.info.difficulty = normalize(item.innerText.split('\n')[1]);
        if(item.querySelector('i.icon-linux') != null){
            trackItem._type = 'mch'
            trackItem.info.os = 'linux'
        } else if(item.querySelector('i.icon-windows') != null) {
            trackItem._type = 'mch'
            trackItem.info.os = 'windows'
        } else {
            trackItem._type = 'shr';
        }
        try {
            trackItem.info.logo = getBackgroundImageUrl(item.querySelector('div[style^="background-image:"]'));
        } catch(error){
             trackItem._type = 'chl';
        }
        track.tasks.push(trackItem);
    })
    printJson(track);
    return track;
}

function getProLab(){
    const proLab = new HtbMachine('lab');
    proLab.info.name = document.querySelector('span.font-size54').innerText;
    proLab.info.logo = document.querySelector('img[src^="/images/icons/ic-prolabs"]').src;

    let overviewCard = Array.from(document.querySelector('span.font-size54').parentElement.nextElementSibling.querySelectorAll('span')).map(e => e.innerText);

    proLab.info.tags.push(`${overviewCard.pop()} (${overviewCard.pop()})`);
    proLab.info[normalize(overviewCard.pop())] = normalize(overviewCard.pop()); // Get difficulty

    function getLabDetails(proLab){
        proLab.entry_point = document.querySelector('span.pt-2.font-size16.fontSemiBold.noWrap.color-green').innerText;
        proLab.info.url = document.URL;
        // Get target machines
        Array.from(document.querySelectorAll('div.machinecard')).forEach(item => {
            let machine = new HtbMachine('mch');
            machine.info.name = item.innerText;
            machine.info.logo = getBackgroundImageUrl(item.querySelector('div[style^="background-image:"]'));
            if(item.querySelector('i.icon-windows') != null){
                machine.info.os = 'windows';
            } else if(item.querySelector('i.icon-linux') != null) {
                machine.info.os = 'linux';
            }
            proLab.about.targets.push(machine);
        });
        // Get tasks
        Array.from(document.querySelector('div.col div.animated.fadeIn').children).forEach(item =>{
            let index = proLab.tasks.length + 1;
            if(item.querySelector('p.flag-intro') != null){
                let card = Array.from(item.querySelector('p.flag-intro').children);
                proLab.info.name = card.splice(0, 1)[0].innerText;
                proLab.info.authors.push(card.splice(0, 1)[0].innerText);
                proLab.info.description = card.map(e=> e.innerText).join('\n');
            } else { // not 'Introduction' section
                proLab.tasks.push(new Task(
                    number=index,
                    text=item.innerText.split('\n')[0],
                    answer=null,
                    points=Number(item.innerText.split('\n')[1].split(' ')[0])
                    )
                )
            }
        });
        printJson(proLab);
        return proLab;
    }
    document.querySelectorAll('div[role="tab"]')[0].click(); // Click 'Lab' button to load corresponding HTML
    setTimeout(getLabDetails, 2000, proLab);
}

function getFortress(){
    const fortress = new HtbMachine('ftr');
    fortress.info.url = document.URL;
    fortress.info.name = document.querySelector('p.htb-text.pr-12').previousElementSibling.innerText.split(' ').pop();
    fortress.info.authors.push(fortress.info.name); // Author and Name have the same value
    fortress.info.difficulty = 'real_scenario';
    fortress.info.logo = document.querySelector('div.fortressBanner img').src;
    fortress.entry_point = document.querySelector('span.pt-2.font-size16.fontSemiBold.noWrap.color-green').innerText;
    fortress.info.description = document.querySelector('p.htb-text.pr-12').innerText;
    fortress.info.points = Number(document.querySelector('div.fortressBanner').innerText.split('\n\n')[2].split(' ')[0]);
    // fortress.completions = Number(document.querySelector('div.fortressBanner').innerText.split('\n\n')[0])

    // Get tasks
    Array.from(document.querySelector('div.col div[class="animated fadeIn"]').children).forEach(item =>{
        if(item.querySelector('p.flag-intro') != null) {
            fortress.info.description = item.querySelector('p.flag-intro').innerText;
        } else {  // not 'Introduction' section
            fortress.tasks.push(new Task(
                    number=fortress.tasks.length + 1,
                    text=item.innerText.split('\n')[0],
                    answer=null,
                    points=Number(item.innerText.split('\n')[1].replace(' POINTS', ''))
                )
            )
        }
    });
    printJson(fortress);
    return fortress;
}

function getBattleground(){
    const btg = new HtbMachine('btg');
    btg.info.url = document.URL;
    // TODO: implement
    console.warn("NOT IMPLEMENTED: getBattleground()");
    return btg
}

// ++============================================++
// ||                  M A I N                   ||
// ++============================================++


function help(){
	console.log([
		'HTB toolkit, by @uRHL',
		'- help()             -> Prints this message and exits',
		'\nCLASSES',
		'- Task               -> Task (title, duration, tier, ...)',
		'- HtbModule          -> Module details (title, duration, tier, ...)',
		'- HtbModule          -> Collections of modules',
		'\nACADEMY PARSERS',
		"- getModule()        -> Get details from module's details page",
		'- listModules()      -> Return a list of modules from modules/ page',
		'- listPaths()        -> Return a list of HtbPath instances',
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
        listPaths();
    } else {
        console.warn('Invalid URL. No data to extract');
        help();
    }
}

main();