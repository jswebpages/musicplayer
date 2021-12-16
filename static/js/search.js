let button = document.querySelector("#submit")
let input = document.querySelector("#search")
let output = document.querySelector("#output")
let finalHTML

function play() {
    var audio = document.getElementById("audio");
    audio.play();
}

button.addEventListener("click", (e)=>{
    getDataFromItunes()
})

function getDataFromItunes(){
    let url = "https://itunes.apple.com/search?term=" + input.value
    
    fetch(url).then(data => data.json()).then(json =>{

        json.results.forEach(song => {
            
            finalHTML +=
            `
            <div>
            <div class="col s6 m4 l3"> <!-- class="col s12 m7"  col s4 m4 l4 -->
              <div class="card">
                <div class="card-image">
                  <img src="${song.artworkUrl100}">
                  <span class="card-title">${song.artistName}</span>
                </div>
                <div class="card-content">
                <ul>
                <li><b>Album:</b> ${song.collectionCensoredName}</li>
                <li><b>Genre:</b> ${song.primaryGenreName}</li>
                <li><b>Song:</b> ${song.trackName}</li>
                </ul>

                </div>
                <div class="card-action" style="background-color: black;">
                <input type="button" value="PLAY" onclick="play()">
                <audio id="audio" src="${song.previewUrl}"></audio>
                </div>
              </div>
            </div>
          </div>
        `
       
        })
        console.log(json) 
        output.innerHTML = finalHTML;        
    })
    .catch(error => console.log(error))
}
