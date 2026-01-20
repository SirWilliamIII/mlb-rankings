
const data = {
    "200": {
        "div_name": "American League West",
        "teams": [
            { "name": "Angels", "w": 0, "l": 0, "gb": "-" }
        ]
    }
};

function render(data, keyword) {
    console.log(`Rendering for ${keyword}`);
    try {
        const leagueDivisions = Object.entries(data)
            .filter(([id, div]) => div.div_name && div.div_name.includes(keyword))
            .sort((a, b) => a[1].div_name.localeCompare(b[1].div_name));

        console.log(`Found ${leagueDivisions.length} divisions`);

        leagueDivisions.forEach(([divId, div]) => {
            const teams = div.teams.sort((a, b) => b.w - a.w);
            teams.forEach((t, idx) => {
                let pct = t.w / (t.w + t.l);
                console.log(`PCT raw: ${pct}`);
                if (isNaN(pct)) pct = 0.000; // Fix NaN
                
                // Original code
                // const pctFixed = pct.toFixed(3).slice(1); 
                // console.log(`Fixed: ${pctFixed}`);
                
                // If pct is 0, toFixed(3) is "0.000", slice(1) is ".000".
                // If pct is NaN, toFixed(3) is "NaN". slice(1) is "aN".
            });
        });
    } catch (e) {
        console.error(e);
    }
}

render(data, 'American');
