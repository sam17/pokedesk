import html from "./index.html";
import tray from "../stl/tray.stl";
import lid from "../stl/lid.stl";
import trayWhite from "../stl/tray_white.stl";
import trayBlack from "../stl/tray_black.stl";
import lidWhite from "../stl/lid_white.stl";
import lidBlack from "../stl/lid_black.stl";

const PREFIX = "/pokedesk/zero-tower";
const files = {
  "tray.stl": tray, "lid.stl": lid,
  "tray_white.stl": trayWhite, "tray_black.stl": trayBlack,
  "lid_white.stl": lidWhite, "lid_black.stl": lidBlack,
};

export default {
  async fetch(request) {
    const path = new URL(request.url).pathname;
    const name = path.startsWith(PREFIX + "/") ? path.slice(PREFIX.length + 1) : "";
    if (files[name]) {
      return new Response(files[name], {
        headers: {
          "content-type": "model/stl",
          "content-disposition": `attachment; filename="pi-zero-tower-${name}"`,
          "cache-control": "public, max-age=3600",
        },
      });
    }
    if (name === "" || name === "index.html") {
      return new Response(html, {
        headers: { "content-type": "text/html;charset=UTF-8", "cache-control": "public, max-age=300" },
      });
    }
    return new Response("not found", { status: 404 });
  },
};
