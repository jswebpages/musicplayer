let mysong = document.getElementById("mysong");
let icon = document.getElementById("icon");

icon.onclick = function(){
    if(mysong.paused){
            mysong.play();
            icon.src = "/static/images/pause.png"
        }else{
            mysong.pause();
            icon.src = "/static/images/play.png";
        } 
}