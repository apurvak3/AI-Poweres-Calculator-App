console.log("Hello, World")n loadModel() {
    model = await mobilenet.load();
    console.log("Model loaded successfully!");
}

async function classifyDrawing() {
    const image = document.getElementById("canvas");
    const prediction = await model.classify(image);
    
    console.log("Prediction:", prediction);
    
    if (prediction.length > 0) {
        alert(`I think you drew a: ${prediction[0].className} (Confidence: ${(prediction[0].probability * 100).toFixed(2)}%)`);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    loadModel();
});
