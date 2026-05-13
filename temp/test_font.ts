import { PDFDocument } from "npm:pdf-lib@1.17.1";

async function main() {
  const pdfDoc = await PDFDocument.create();
  console.log("Fetching font...");
  const fontRes = await fetch("https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Regular.ttf");
  const fontBytes = await fontRes.arrayBuffer();
  
  console.log("Embedding font...");
  const customFont = await pdfDoc.embedFont(fontBytes);
  
  const page = pdfDoc.addPage();
  page.drawText("Салом Дунё! (Hello World in Cyrillic)", {
    x: 50,
    y: 700,
    size: 20,
    font: customFont
  });
  
  const pdfBytes = await pdfDoc.save();
  await Deno.writeFile("test_cyrillic.pdf", pdfBytes);
  console.log("Success! check test_cyrillic.pdf");
}

main();
