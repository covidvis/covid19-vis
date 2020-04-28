

function makePopulateInfoPageSpaceHandler(tabId){
	var possibleValues = new Set();
	function makeInfoPage(value) {
		if (possibleValues.has(value)) {
			return;
		}
		if (!(value in stateDetails)) {
			return;
		}
		possibleValues.add(value);
		var infoPage = document.createElement("div");
		var infoList = document.createElement("ul");
		infoPage.id = value.split(" ").join("_")+"_"+tabId;
		infoPage.className = "infoPage";

		var chartDiv = document.getElementById(tabId);
		chartDiv.appendChild(infoPage);
		infoPage.appendChild(infoList);
		infoList.innerHTML = stateDetails[value];
	}

	var oldValue = null;
	return function(name, value) {
		// Turn off old value first
		// Then turn on the page corresponding to the selected dropdown option
        if (oldValue !== null) {
			for (let k in oldValue) {
				if (!k.startsWith('Select_')) {
					continue;
				}
				var groups = oldValue[k];
				for (let group of groups) {
					var pageName = group.split(" ").join("_")+"_"+tabId;
					$("#"+pageName).hide();
				}
			}
		}
        oldValue = value;
		for (let k in value) {
			if (!k.startsWith('Select_')) {
				continue;
			}
			var groups = value[k];
			for (let group of groups) {
				makeInfoPage(group);
				var pageName = group.split(" ").join("_")+"_"+tabId;
				$("#"+pageName).show();
			}
		}
	};
}
