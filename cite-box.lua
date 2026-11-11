--[[
cite-box.lua: "Cite this post" for pages whose front matter has a `cite:` block.

  cite:
    url: https://vahhabpiranfar.com/posts/<slug>/
    site: Vahhab Piranfar          # website title (container)
    place: Jersey City (NJ)        # optional, Vancouver place of publication
    title-sentence: ...            # optional, APA sentence-case title when the automatic one is wrong

Adds:
  * citation_* (Highwire) and DC.* meta tags, read by the Zotero, Mendeley and EndNote browser tools;
  * a JSON data block and a mount under the title, filled by cite-box.js (button + popover with
    Vancouver, APA, MLA, BibTeX and RIS, copy and .ris/.bib downloads);
  * a "How to cite" section before "References" (or at the end), with a plain Vancouver fallback
    for readers without JavaScript.
Pages without `cite:` are left untouched.
]]

local str = pandoc.utils.stringify
local MON3 = { "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" }

local function esc(s)
  return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

local function json(v)
  if quarto and quarto.json then return quarto.json.encode(v) end
  return pandoc.json.encode(v)
end

-- authors as {given, family, literal, orcid, affiliation}
local function authors(meta)
  local out = {}
  local src = meta["by-author"] or meta.author or meta.authors
  if not src then return out end
  if pandoc.utils.type(src) ~= "List" then src = { src } end
  for _, a in ipairs(src) do
    local given, family, literal, orcid, aff = "", "", "", "", ""
    if type(a) == "table" and a.name ~= nil then
      local n = a.name
      if type(n) == "table" and (n.given or n.family or n.literal) then
        given = n.given and str(n.given) or ""
        family = n.family and str(n.family) or ""
        literal = n.literal and str(n.literal) or ""
      else
        literal = str(n)
      end
      orcid = a.orcid and str(a.orcid) or ""
      local affs = a.affiliations or a.affiliation
      if affs then
        if pandoc.utils.type(affs) == "List" then affs = affs[1] end
        if type(affs) == "table" and affs.name then aff = str(affs.name) else aff = str(affs) end
      end
    else
      literal = str(a)
    end
    if literal == "" then literal = (given .. " " .. family):gsub("^%s+", ""):gsub("%s+$", "") end
    if family == "" then
      given, family = literal:match("^(.-)%s*(%S+)$")
      given, family = given or "", family or literal
    end
    table.insert(out, { given = given, family = family, literal = literal, orcid = orcid, affiliation = aff })
  end
  return out
end

local function initials(given)
  local s = ""
  for w in given:gmatch("[^%s%-]+") do s = s .. w:sub(1, 1):upper() end
  return s
end

function Pandoc(doc)
  local meta = doc.meta
  if not meta.cite then return nil end
  local c = meta.cite
  local url = c.url and str(c.url) or ""
  local site = c.site and str(c.site) or "Vahhab Piranfar"
  local place = c.place and str(c.place) or ""
  local title = meta.title and str(meta.title) or ""
  -- Quarto may already have formatted the date ("November 10, 2026"); accept that or ISO
  local date = meta.date and str(meta.date) or ""
  local y, m, d = date:match("^(%d%d%d%d)%-(%d%d)%-(%d%d)")
  if not y then
    local MONTHS = { January = 1, February = 2, March = 3, April = 4, May = 5, June = 6, July = 7,
      August = 8, September = 9, October = 10, November = 11, December = 12 }
    local mn, dd, yy = date:match("^(%a+)%s+(%d+),%s*(%d%d%d%d)$")
    if mn and MONTHS[mn] then
      y, m, d = yy, string.format("%02d", MONTHS[mn]), string.format("%02d", tonumber(dd))
    end
  end
  if y then date = y .. "-" .. m .. "-" .. d end
  local auth = authors(meta)
  local keywords = {}
  if meta.categories then
    for _, k in ipairs(meta.categories) do table.insert(keywords, str(k)) end
  end

  local data = {
    title = title,
    titleSentence = c["title-sentence"] and str(c["title-sentence"]) or "",
    abstract = meta.description and str(meta.description) or "",
    date = date, url = url, site = site, place = place,
    authors = auth, keywords = keywords,
  }

  -- header meta tags (Highwire Press + Dublin Core)
  local h = {}
  local function tag(name, content)
    if content and content ~= "" then
      table.insert(h, string.format('<meta name="%s" content="%s">', name, esc(content)))
    end
  end
  tag("citation_title", title)
  for _, a in ipairs(auth) do
    tag("citation_author", a.family .. ", " .. a.given)
    tag("citation_author_institution", a.affiliation)
    tag("citation_author_orcid", a.orcid ~= "" and ("https://orcid.org/" .. a.orcid) or "")
  end
  if y then
    tag("citation_publication_date", y .. "/" .. m .. "/" .. d)
    tag("citation_online_date", y .. "/" .. m .. "/" .. d)
  end
  tag("citation_publisher", site)
  tag("citation_language", "en")
  tag("citation_public_url", url)
  tag("citation_abstract", data.abstract)
  tag("citation_keywords", table.concat(keywords, "; "))
  tag("DC.title", title)
  for _, a in ipairs(auth) do tag("DC.creator", a.family .. ", " .. a.given) end
  tag("DC.date", date)
  tag("DC.publisher", site)
  tag("DC.identifier", url)
  tag("DC.language", "en")
  quarto.doc.include_text("in-header", table.concat(h, "\n"))

  quarto.doc.add_html_dependency({
    name = "cite-box", version = "1.0.0",
    scripts = { "cite-box.js" }, stylesheets = { "cite-box.css" },
  })

  -- plain Vancouver fallback (JavaScript replaces it with the full panel)
  local names = {}
  for _, a in ipairs(auth) do table.insert(names, a.family .. " " .. initials(a.given)) end
  local when = y and string.format("%s %s %d", y, MON3[tonumber(m)], tonumber(d)) or date
  local pub = (place ~= "" and (place .. ": ") or "") .. site .. "; " .. when
  local fallback = string.format("%s. %s [Internet]. %s. Available from: %s",
    table.concat(names, ", "), title, pub, url)

  local top = pandoc.RawBlock("html",
    '<script type="application/json" id="cite-data">' .. json(data):gsub("</", "<\\/") .. '</script>\n' ..
    '<div class="cite-top-mount" hidden></div>')
  table.insert(doc.blocks, 1, top)

  local section = {
    pandoc.Header(2, "How to cite", pandoc.Attr("how-to-cite")),
    pandoc.RawBlock("html",
      '<div class="cite-inline-mount"><p class="cite-fallback">' .. esc(fallback) .. '</p></div>'),
  }
  local at = nil
  for i, b in ipairs(doc.blocks) do
    if b.t == "Header" and b.level == 2 and b.identifier == "references" then at = i break end
  end
  if at then
    for j = #section, 1, -1 do table.insert(doc.blocks, at, section[j]) end
  else
    for _, b in ipairs(section) do table.insert(doc.blocks, b) end
  end
  return doc
end
