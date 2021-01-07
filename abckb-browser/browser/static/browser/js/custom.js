function hide_spaceship(enterprise) {
    document.getElementById(enterprise).style.visibility = "hidden";
}

function show_spaceship(enterprise) {
    document.getElementById(enterprise).style.visibility = "visible";
}

function open_discovery()
{
   console.log("Open discovery");
   var x = document.getElementById("opendis");
   var y = document.getElementById("closedis");

   if (x.style.visibility == "visible" && y.style.visibility == "hidden") {
        hideTable(x);
    } else if (x.style.visibility == "hidden" && y.style.visibility == "visible") {
        showTable(x);
        hideTable(y);
    } else {
        showTable(x)
    }
}

function closed_discovery()
{
    console.log("Closed discovery");
    var y = document.getElementById("opendis");
    var x = document.getElementById("closedis");
 
    if (x.style.visibility === "visible" && y.style.visibility === "hidden") {
         hideTable(x);
     } else if (x.style.visibility === "hidden" && y.style.visibility === "visible") {
         showTable(x);
         hideTable(y);
     } else {
         showTable(x)
     }
 }

function showTable(item){
    console.log("showing" + item)
    item.style.visibility = "visible";
}

function hideTable(item){
    console.log("hiding" + item)
    item.style.visibility = "hidden";
}