

function getDropdownValues(mData) {
	let arry = [];
	for (let index = 0; index < mData.children.length; index++) {
	    arry.push(mData.children[index].value);
	}
	return arry;
}
// $( document ).ready(function() {

// })
function populateInfoPages(tabId){
	var chartDiv = document.getElementById(tabId)
	var selector = "#"+tabId+" > div > div:nth-child(2) > select"
	var possibleValues = getDropdownValues($(selector)[0])
	for (let val of possibleValues){
		var infoPage = document.createElement("div")
		var infoList = document.createElement("ul")
		infoPage.id = val.split(" ").join("_")+"_"+tabId
		infoPage.className = "infoPage"

		chartDiv.appendChild(infoPage)
		infoPage.appendChild(infoList)
		infoList.innerHTML = stateDetails[val]
	}

	$(selector).on('change', function() {
		// Turn everything off first
		for (let val of possibleValues){
			var pgName = val.split(" ").join("_")+"_"+tabId
			if (pgName){
				$("#"+pgName).hide();
			}
		}
		// Then turn on the page corresponding to the selected dropdown option
		var pageName = this.value.split(" ").join("_")+"_"+tabId
		$("#"+pageName).show();

	});
}
// populateInfoPages("jhu_world_cases")
// populateInfoPages("jhu_world_deaths")
// populateInfoPages("jhu_us_cases")
// populateInfoPages("jhu_us_deaths")