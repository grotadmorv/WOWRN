local ADDON_NAME, ADDON_NS = ...

local CatalogUI = {}
ADDON_NS.CatalogUI = CatalogUI

local FRAME_WIDTH = 800
local FRAME_HEIGHT = 600
local ITEM_HEIGHT = 24
local ITEMS_PER_PAGE = 20

local CLASS_INFO = {
    ["death-knight"] = { name = "Death Knight", color = "C41E3A", icon = "Interface\\Icons\\Spell_Deathknight_ClassIcon" },
    ["demon-hunter"] = { name = "Demon Hunter", color = "A330C9", icon = "Interface\\Icons\\ClassIcon_DemonHunter" },
    ["druid"] = { name = "Druid", color = "FF7C0A", icon = "Interface\\Icons\\ClassIcon_Druid" },
    ["evoker"] = { name = "Evoker", color = "33937F", icon = "Interface\\Icons\\ClassIcon_Evoker" },
    ["hunter"] = { name = "Hunter", color = "AAD372", icon = "Interface\\Icons\\ClassIcon_Hunter" },
    ["mage"] = { name = "Mage", color = "3FC7EB", icon = "Interface\\Icons\\ClassIcon_Mage" },
    ["monk"] = { name = "Monk", color = "00FF98", icon = "Interface\\Icons\\ClassIcon_Monk" },
    ["paladin"] = { name = "Paladin", color = "F48CBA", icon = "Interface\\Icons\\ClassIcon_Paladin" },
    ["priest"] = { name = "Priest", color = "FFFFFF", icon = "Interface\\Icons\\ClassIcon_Priest" },
    ["rogue"] = { name = "Rogue", color = "FFF468", icon = "Interface\\Icons\\ClassIcon_Rogue" },
    ["shaman"] = { name = "Shaman", color = "0070DD", icon = "Interface\\Icons\\ClassIcon_Shaman" },
    ["warlock"] = { name = "Warlock", color = "8788EE", icon = "Interface\\Icons\\ClassIcon_Warlock" },
    ["warrior"] = { name = "Warrior", color = "C69B6D", icon = "Interface\\Icons\\ClassIcon_Warrior" },
}

local SPEC_NAMES = {
    -- Death Knight
    ["blood"] = "Blood",
    ["frost"] = "Frost",
    ["unholy"] = "Unholy",
    -- Demon Hunter
    ["havoc"] = "Havoc",
    ["vengeance"] = "Vengeance",
    ["devourer"] = "Devourer",
    -- Druid
    ["balance"] = "Balance",
    ["feral"] = "Feral",
    ["guardian"] = "Guardian",
    ["restoration"] = "Restoration",
    -- Evoker
    ["devastation"] = "Devastation",
    ["preservation"] = "Preservation",
    ["augmentation"] = "Augmentation",
    -- Hunter
    ["beast-mastery"] = "Beast Mastery",
    ["marksmanship"] = "Marksmanship",
    ["survival"] = "Survival",
    -- Mage
    ["arcane"] = "Arcane",
    ["fire"] = "Fire",
    -- Monk
    ["brewmaster"] = "Brewmaster",
    ["mistweaver"] = "Mistweaver",
    ["windwalker"] = "Windwalker",
    -- Paladin
    ["holy"] = "Holy",
    ["protection"] = "Protection",
    ["retribution"] = "Retribution",
    -- Priest
    ["discipline"] = "Discipline",
    ["shadow"] = "Shadow",
    -- Rogue
    ["assassination"] = "Assassination",
    ["outlaw"] = "Outlaw",
    ["subtlety"] = "Subtlety",
    -- Shaman
    ["elemental"] = "Elemental",
    ["enhancement"] = "Enhancement",
    -- Warlock
    ["affliction"] = "Affliction",
    ["demonology"] = "Demonology",
    ["destruction"] = "Destruction",
    -- Warrior
    ["arms"] = "Arms",
    ["fury"] = "Fury",
}

local TIER_COLORS = {
    ["S"] = { r = 1, g = 0.5, b = 0 },       -- Orange
    ["A"] = { r = 0.64, g = 0.21, b = 0.93 }, -- Purple
    ["B"] = { r = 0, g = 0.44, b = 0.87 },   -- Blue
    ["C"] = { r = 0.12, g = 1, b = 0 },      -- Green
    ["D"] = { r = 1, g = 1, b = 1 },         -- White
    ["F"] = { r = 0.62, g = 0.62, b = 0.62 }, -- Gray
}

local DATA_SOURCES = {
    { key = "wowhead", name = "WoWHead", color = {1, 0.5, 0}, available = true },
    { key = "icyveins", name = "Icy Veins", color = {0.4, 0.8, 1}, available = false },
    { key = "bloodmallet", name = "Bloodmallet", color = {0.8, 0.2, 0.2}, available = false },
}

local selectedSource = "wowhead"

local mainFrame = nil
local selectedClass = nil
local selectedSpec = nil
local selectedCategory = "bis"
local selectedContext = "Overall"
local scrollOffset = 0
local currentItems = {}

local function GetClassColor(classKey)
    local info = CLASS_INFO[classKey]
    if info then
        local r = tonumber(info.color:sub(1, 2), 16) / 255
        local g = tonumber(info.color:sub(3, 4), 16) / 255
        local b = tonumber(info.color:sub(5, 6), 16) / 255
        return r, g, b
    end
    return 1, 1, 1
end

local function CreateItemLink(itemId)
    return "|Hitem:" .. itemId .. "::::::::::::::::|h"
end

local function CreateCustomTooltip()
    if customTooltip then return customTooltip end

    local tooltip = CreateFrame("Frame", "WOWRNCustomTooltip", UIParent, "BackdropTemplate")
    tooltip:SetSize(320, 180)
    tooltip:SetFrameStrata("TOOLTIP")
    tooltip:SetFrameLevel(100)
    tooltip:Hide()

    tooltip:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8x8",
        edgeFile = "Interface\\Buttons\\WHITE8x8",
        edgeSize = 2,
    })
    tooltip:SetBackdropColor(0.08, 0.08, 0.1, 0.95)
    tooltip:SetBackdropBorderColor(0.6, 0.5, 0.2, 1)

    local innerBorder = CreateFrame("Frame", nil, tooltip, "BackdropTemplate")
    innerBorder:SetPoint("TOPLEFT", 2, -2)
    innerBorder:SetPoint("BOTTOMRIGHT", -2, 2)
    innerBorder:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8x8",
        edgeFile = "Interface\\Buttons\\WHITE8x8",
        edgeSize = 1,
    })
    innerBorder:SetBackdropColor(0, 0, 0, 0)
    innerBorder:SetBackdropBorderColor(0.3, 0.25, 0.1, 0.5)

    local headerBg = tooltip:CreateTexture(nil, "ARTWORK")
    headerBg:SetSize(316, 28)
    headerBg:SetPoint("TOP", tooltip, "TOP", 0, -2)
    headerBg:SetColorTexture(0.15, 0.12, 0.05, 0.9)
    tooltip.headerBg = headerBg

    local headerText = tooltip:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    headerText:SetPoint("TOP", tooltip, "TOP", 0, -8)
    headerText:SetText("|cFFFFD700[WOWRN]|r Item Info")
    tooltip.headerText = headerText

    local iconFrame = CreateFrame("Frame", nil, tooltip, "BackdropTemplate")
    iconFrame:SetSize(44, 44)
    iconFrame:SetPoint("TOPLEFT", tooltip, "TOPLEFT", 12, -38)
    iconFrame:SetBackdrop({
        bgFile = "Interface\\Buttons\\WHITE8x8",
        edgeFile = "Interface\\Buttons\\WHITE8x8",
        edgeSize = 2,
    })
    iconFrame:SetBackdropColor(0, 0, 0, 0.8)
    iconFrame:SetBackdropBorderColor(0.4, 0.4, 0.4, 1)

    local icon = iconFrame:CreateTexture(nil, "ARTWORK")
    icon:SetSize(40, 40)
    icon:SetPoint("CENTER")
    icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    tooltip.icon = icon
    tooltip.iconFrame = iconFrame

    local itemName = tooltip:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    itemName:SetPoint("TOPLEFT", iconFrame, "TOPRIGHT", 10, -2)
    itemName:SetPoint("RIGHT", tooltip, "RIGHT", -12, 0)
    itemName:SetJustifyH("LEFT")
    itemName:SetWordWrap(true)
    tooltip.itemName = itemName

    local itemType = tooltip:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    itemType:SetPoint("TOPLEFT", itemName, "BOTTOMLEFT", 0, -4)
    itemType:SetTextColor(0.7, 0.7, 0.7)
    tooltip.itemType = itemType

    local separator = tooltip:CreateTexture(nil, "ARTWORK")
    separator:SetSize(296, 1)
    separator:SetPoint("TOP", tooltip, "TOP", 0, -90)
    separator:SetColorTexture(0.4, 0.35, 0.2, 0.6)
    tooltip.separator = separator

    local infoContainer = CreateFrame("Frame", nil, tooltip)
    infoContainer:SetSize(296, 60)
    infoContainer:SetPoint("TOP", separator, "BOTTOM", 0, -8)
    tooltip.infoContainer = infoContainer

    tooltip.infoLines = {}
    for i = 1, 4 do
        local line = CreateFrame("Frame", nil, infoContainer)
        line:SetSize(296, 18)
        line:SetPoint("TOP", infoContainer, "TOP", 0, -(i-1) * 20)

        local label = line:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
        label:SetPoint("LEFT", line, "LEFT", 0, 0)
        label:SetTextColor(0.6, 0.6, 0.6)
        line.label = label

        local value = line:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
        value:SetPoint("RIGHT", line, "RIGHT", 0, 0)
        line.value = value

        tooltip.infoLines[i] = line
    end

    local hint = tooltip:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    hint:SetPoint("BOTTOM", tooltip, "BOTTOM", 0, 8)
    hint:SetText("|cFF888888Shift+Click to link in chat|r")
    tooltip.hint = hint

    customTooltip = tooltip
    return tooltip
end

local function ShowCustomTooltip(parent, itemData)
    local tooltip = CreateCustomTooltip()
    tooltip:ClearAllPoints()
    tooltip:SetPoint("LEFT", parent, "RIGHT", 15, 0)

    local itemId = tonumber(itemData.id)
    local itemName, itemLink, itemQuality, _, _, itemType, itemSubType, _, _, itemTexture = GetItemInfo(itemId or 0)

    if itemTexture then
        tooltip.icon:SetTexture(itemTexture)
    else
        tooltip.icon:SetTexture("Interface\\Icons\\INV_Misc_QuestionMark")
    end

    if itemQuality then
        local r, g, b = GetItemQualityColor(itemQuality)
        tooltip.iconFrame:SetBackdropBorderColor(r, g, b, 1)
        tooltip.itemName:SetText(itemData.name or "Unknown Item")
        tooltip.itemName:SetTextColor(r, g, b)
    else
        tooltip.iconFrame:SetBackdropBorderColor(0.6, 0.6, 0.6, 1)
        tooltip.itemName:SetText(itemData.name or "Unknown Item")
        tooltip.itemName:SetTextColor(1, 1, 1)
    end

    if itemType and itemSubType then
        tooltip.itemType:SetText(itemSubType)
    else
        tooltip.itemType:SetText("")
    end

    for _, line in ipairs(tooltip.infoLines) do
        line.label:SetText("")
        line.value:SetText("")
        line:Hide()
    end

    local lineIndex = 1

    if itemData.type == "trinket" then
        local tierColor = TIER_COLORS[itemData.tier] or TIER_COLORS["D"]
        tooltip.infoLines[lineIndex].label:SetText("Tier Ranking")
        tooltip.infoLines[lineIndex].value:SetText(itemData.tier .. " Tier")
        tooltip.infoLines[lineIndex].value:SetTextColor(tierColor.r, tierColor.g, tierColor.b)
        tooltip.infoLines[lineIndex]:Show()
        lineIndex = lineIndex + 1
    elseif itemData.type == "bis" then
        tooltip.infoLines[lineIndex].label:SetText("Equipment Slot")
        tooltip.infoLines[lineIndex].value:SetText(itemData.slot or "Unknown")
        tooltip.infoLines[lineIndex].value:SetTextColor(0.3, 1, 0.3)
        tooltip.infoLines[lineIndex]:Show()
        lineIndex = lineIndex + 1

        tooltip.infoLines[lineIndex].label:SetText("Best For")
        tooltip.infoLines[lineIndex].value:SetText(itemData.context or "Overall")
        tooltip.infoLines[lineIndex].value:SetTextColor(1, 0.82, 0)
        tooltip.infoLines[lineIndex]:Show()
        lineIndex = lineIndex + 1
    elseif itemData.type == "cartel" then
        tooltip.infoLines[lineIndex].label:SetText("Cartel Chip")
        tooltip.infoLines[lineIndex].value:SetText(itemData.details or "Mythic")
        tooltip.infoLines[lineIndex].value:SetTextColor(0.5, 0.8, 1)
        tooltip.infoLines[lineIndex]:Show()
        lineIndex = lineIndex + 1
    end

    tooltip.infoLines[lineIndex].label:SetText("Data Source")
    tooltip.infoLines[lineIndex].value:SetText("WoWHead")
    tooltip.infoLines[lineIndex].value:SetTextColor(1, 0.5, 0)
    tooltip.infoLines[lineIndex]:Show()
    lineIndex = lineIndex + 1
    tooltip.infoLines[lineIndex].label:SetText("Item ID")
    tooltip.infoLines[lineIndex].value:SetText(tostring(itemData.id))
    tooltip.infoLines[lineIndex].value:SetTextColor(0.5, 0.5, 0.5)
    tooltip.infoLines[lineIndex]:Show()
    local height = 100 + (lineIndex * 20) + 30
    tooltip:SetSize(320, height)
    tooltip.separator:SetPoint("TOP", tooltip, "TOP", 0, -90)

    tooltip:Show()
end

local function HideCustomTooltip()
    if customTooltip then
        customTooltip:Hide()
    end
end

local function BuildItemList()
    currentItems = {}
    
    if not TierListAddonData or not selectedClass or not selectedSpec then
        return
    end
    
    local classData = TierListAddonData[selectedClass]
    if not classData then return end
    
    local specData = classData[selectedSpec]
    if not specData then return end
    
    if selectedCategory == "bis" then
        if specData.bis and specData.bis[selectedContext] then
            for _, item in ipairs(specData.bis[selectedContext]) do
                table.insert(currentItems, {
                    id = item.id,
                    name = item.name,
                    slot = item.slot,
                    type = "bis",
                    context = selectedContext,
                })
            end
        end
    elseif selectedCategory == "trinkets" then
        if specData.trinkets then
            for tier, items in pairs(specData.trinkets) do
                for _, item in ipairs(items) do
                    table.insert(currentItems, {
                        id = item.id,
                        name = item.name,
                        tier = tier,
                        type = "trinket",
                    })
                end
            end
            local tierOrder = { S = 1, A = 2, B = 3, C = 4, D = 5, F = 6 }
            table.sort(currentItems, function(a, b)
                return (tierOrder[a.tier] or 99) < (tierOrder[b.tier] or 99)
            end)
        end
    elseif selectedCategory == "cartel_chips" then
        if specData.cartel_chips then
            for _, item in ipairs(specData.cartel_chips) do
                table.insert(currentItems, {
                    id = item.id,
                    name = item.name,
                    details = item.details,
                    type = "cartel",
                })
            end
        end
    end
end

local function GetSpecsForClass(classKey)
    local specs = {}
    if TierListAddonData and TierListAddonData[classKey] then
        for specKey, _ in pairs(TierListAddonData[classKey]) do
            table.insert(specs, specKey)
        end
    end
    table.sort(specs)
    return specs
end

local function GetAvailableContexts()
    local contexts = {}
    if TierListAddonData and selectedClass and selectedSpec then
        local specData = TierListAddonData[selectedClass][selectedSpec]
        if specData and specData.bis then
            for context, _ in pairs(specData.bis) do
                table.insert(contexts, context)
            end
        end
    end
    table.sort(contexts)
    return contexts
end

local function CreateMainFrame()
    if mainFrame then return mainFrame end
    
    mainFrame = CreateFrame("Frame", "WOWRNCatalogFrame", UIParent, "BasicFrameTemplateWithInset")
    mainFrame:SetSize(FRAME_WIDTH, FRAME_HEIGHT)
    mainFrame:SetPoint("CENTER")
    mainFrame:SetMovable(true)
    mainFrame:EnableMouse(true)
    mainFrame:RegisterForDrag("LeftButton")
    mainFrame:SetScript("OnDragStart", mainFrame.StartMoving)
    mainFrame:SetScript("OnDragStop", mainFrame.StopMovingOrSizing)
    mainFrame:SetFrameStrata("HIGH")
    mainFrame:Hide()
    
    mainFrame.TitleText:SetText("WOWRN - Tier List Catalog")
    
    tinsert(UISpecialFrames, "WOWRNCatalogFrame")
    
    local leftPanel = CreateFrame("Frame", nil, mainFrame, "InsetFrameTemplate")
    leftPanel:SetSize(180, FRAME_HEIGHT - 60)
    leftPanel:SetPoint("TOPLEFT", mainFrame, "TOPLEFT", 8, -28)
    mainFrame.leftPanel = leftPanel
    
    local leftTitle = leftPanel:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    leftTitle:SetPoint("TOP", leftPanel, "TOP", 0, -8)
    leftTitle:SetText("Classes")
    
    local classScroll = CreateFrame("ScrollFrame", nil, leftPanel, "UIPanelScrollFrameTemplate")
    classScroll:SetSize(155, FRAME_HEIGHT - 100)
    classScroll:SetPoint("TOP", leftTitle, "BOTTOM", -10, -8)
    
    local classContent = CreateFrame("Frame", nil, classScroll)
    classContent:SetSize(155, 500)
    classScroll:SetScrollChild(classContent)
    mainFrame.classContent = classContent
    
    local rightPanel = CreateFrame("Frame", nil, mainFrame, "InsetFrameTemplate")
    rightPanel:SetSize(FRAME_WIDTH - 210, FRAME_HEIGHT - 60)
    rightPanel:SetPoint("TOPRIGHT", mainFrame, "TOPRIGHT", -8, -28)
    mainFrame.rightPanel = rightPanel

    local sourceBar = CreateFrame("Frame", nil, rightPanel)
    sourceBar:SetSize(FRAME_WIDTH - 230, 28)
    sourceBar:SetPoint("TOPLEFT", rightPanel, "TOPLEFT", 10, -5)

    local sourceBg = sourceBar:CreateTexture(nil, "BACKGROUND")
    sourceBg:SetAllPoints()
    sourceBg:SetColorTexture(0.1, 0.1, 0.1, 0.8)

    local sourceLabel = sourceBar:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    sourceLabel:SetPoint("LEFT", sourceBar, "LEFT", 8, 0)
    sourceLabel:SetText("Source:")
    sourceLabel:SetTextColor(0.7, 0.7, 0.7)

    mainFrame.sourceButtons = {}
    local sourceXOffset = 55

    for _, source in ipairs(DATA_SOURCES) do
        local btn = CreateFrame("Button", nil, sourceBar)
        btn:SetSize(85, 22)
        btn:SetPoint("LEFT", sourceBar, "LEFT", sourceXOffset, 0)

        local btnBg = btn:CreateTexture(nil, "BACKGROUND")
        btnBg:SetAllPoints()
        btn.bg = btnBg

        local btnText = btn:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
        btnText:SetPoint("CENTER")
        btn.text = btnText

        if source.available then
            if selectedSource == source.key then
                btnBg:SetColorTexture(source.color[1] * 0.4, source.color[2] * 0.4, source.color[3] * 0.4, 0.9)
                btnText:SetText(source.name)
                btnText:SetTextColor(source.color[1], source.color[2], source.color[3])
            else
                btnBg:SetColorTexture(0.15, 0.15, 0.15, 0.8)
                btnText:SetText(source.name)
                btnText:SetTextColor(0.6, 0.6, 0.6)
            end

            btn:SetScript("OnEnter", function(self)
                if selectedSource ~= source.key then
                    self.bg:SetColorTexture(0.25, 0.25, 0.25, 0.9)
                end
            end)

            btn:SetScript("OnLeave", function(self)
                if selectedSource ~= source.key then
                    self.bg:SetColorTexture(0.15, 0.15, 0.15, 0.8)
                end
            end)

            btn:SetScript("OnClick", function(self)
                selectedSource = source.key
                CatalogUI:UpdateSourceButtons()
                CatalogUI:UpdateItemList()
            end)
        else
            btnBg:SetColorTexture(0.08, 0.08, 0.08, 0.6)
            btnText:SetText(source.name)
            btnText:SetTextColor(0.4, 0.4, 0.4)

            local comingSoon = btn:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
            comingSoon:SetPoint("TOP", btn, "BOTTOM", 0, 2)
            comingSoon:SetText("Soon")
            comingSoon:SetTextColor(0.5, 0.5, 0.5)
            comingSoon:SetScale(0.7)

            btn:SetScript("OnEnter", function(self)
                GameTooltip:SetOwner(self, "ANCHOR_TOP")
                GameTooltip:SetText(source.name, source.color[1], source.color[2], source.color[3])
                GameTooltip:AddLine("Coming Soon!", 0.7, 0.7, 0.7)
                GameTooltip:Show()
            end)

            btn:SetScript("OnLeave", function(self)
                GameTooltip:Hide()
            end)
        end

        btn.sourceKey = source.key
        table.insert(mainFrame.sourceButtons, btn)
        sourceXOffset = sourceXOffset + 90
    end

    mainFrame.sourceBar = sourceBar

    local tabContainer = CreateFrame("Frame", nil, rightPanel)
    tabContainer:SetSize(FRAME_WIDTH - 230, 30)
    tabContainer:SetPoint("TOPLEFT", sourceBar, "BOTTOMLEFT", 0, -5)
    mainFrame.tabContainer = tabContainer
    
    local contextLabel = rightPanel:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    contextLabel:SetPoint("TOPLEFT", tabContainer, "BOTTOMLEFT", 0, -5)
    contextLabel:SetText("Context:")
    mainFrame.contextLabel = contextLabel
    
    local itemScroll = CreateFrame("ScrollFrame", nil, rightPanel, "UIPanelScrollFrameTemplate")
    itemScroll:SetSize(FRAME_WIDTH - 250, FRAME_HEIGHT - 180)
    itemScroll:SetPoint("TOPLEFT", contextLabel, "BOTTOMLEFT", 0, -30)
    
    local itemContent = CreateFrame("Frame", nil, itemScroll)
    itemContent:SetSize(FRAME_WIDTH - 250, 800)
    itemScroll:SetScrollChild(itemContent)
    mainFrame.itemContent = itemContent
    mainFrame.itemScroll = itemScroll
    
    local infoText = rightPanel:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    infoText:SetPoint("CENTER", rightPanel, "CENTER", 0, 0)
    infoText:SetText("Select a class and specialization\nfrom the left panel")
    infoText:SetJustifyH("CENTER")
    mainFrame.infoText = infoText
    
    return mainFrame
end

local function CreateClassButton(parent, classKey, yOffset)
    local info = CLASS_INFO[classKey]
    if not info then return nil, yOffset end
    
    local btn = CreateFrame("Button", nil, parent)
    btn:SetSize(150, 28)
    btn:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -yOffset)
    
    local bg = btn:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(0.1, 0.1, 0.1, 0.8)
    btn.bg = bg
    
    local highlight = btn:CreateTexture(nil, "HIGHLIGHT")
    highlight:SetAllPoints()
    highlight:SetColorTexture(0.3, 0.3, 0.3, 0.5)
    
    local icon = btn:CreateTexture(nil, "ARTWORK")
    icon:SetSize(22, 22)
    icon:SetPoint("LEFT", btn, "LEFT", 4, 0)
    icon:SetTexture(info.icon)
    
    local text = btn:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    text:SetPoint("LEFT", icon, "RIGHT", 6, 0)
    text:SetText(info.name)
    local r, g, b = GetClassColor(classKey)
    text:SetTextColor(r, g, b)
    
    btn.classKey = classKey
    btn:SetScript("OnClick", function(self)
        selectedClass = self.classKey
        selectedSpec = nil
        CatalogUI:UpdateSpecButtons()
        CatalogUI:UpdateItemList()
    end)
    
    return btn, yOffset + 30
end

local function CreateSpecButton(parent, specKey, yOffset)
    local displayName = SPEC_NAMES[specKey] or specKey
    
    local btn = CreateFrame("Button", nil, parent)
    btn:SetSize(140, 24)
    btn:SetPoint("TOPLEFT", parent, "TOPLEFT", 10, -yOffset)
    
    local bg = btn:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(0.15, 0.15, 0.15, 0.8)
    btn.bg = bg
    
    local selected = btn:CreateTexture(nil, "ARTWORK")
    selected:SetSize(4, 20)
    selected:SetPoint("LEFT", btn, "LEFT", 2, 0)
    selected:SetColorTexture(1, 0.82, 0, 1)
    selected:Hide()
    btn.selected = selected
    
    local highlight = btn:CreateTexture(nil, "HIGHLIGHT")
    highlight:SetAllPoints()
    highlight:SetColorTexture(0.4, 0.4, 0.4, 0.5)
    
    local text = btn:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    text:SetPoint("LEFT", btn, "LEFT", 10, 0)
    text:SetText("  " .. displayName)
    
    btn.specKey = specKey
    btn:SetScript("OnClick", function(self)
        selectedSpec = self.specKey
        selectedCategory = "bis"
        selectedContext = "Overall"
        CatalogUI:UpdateSpecButtons()
        CatalogUI:UpdateCategoryTabs()
        CatalogUI:UpdateItemList()
    end)
    
    return btn, yOffset + 26
end

local function CreateCategoryTab(parent, category, displayName, xOffset)
    local btn = CreateFrame("Button", nil, parent)
    btn:SetSize(100, 25)
    btn:SetPoint("LEFT", parent, "LEFT", xOffset, 0)
    
    local bg = btn:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(0.2, 0.2, 0.2, 0.8)
    btn.bg = bg
    
    local text = btn:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    text:SetPoint("CENTER")
    text:SetText(displayName)
    btn.text = text
    
    btn.category = category
    btn:SetScript("OnClick", function(self)
        selectedCategory = self.category
        if selectedCategory == "bis" then
            selectedContext = "Overall"
        end
        CatalogUI:UpdateCategoryTabs()
        CatalogUI:UpdateContextButtons()
        CatalogUI:UpdateItemList()
    end)
    
    return btn
end

local function CreateContextButton(parent, context, xOffset)
    local btn = CreateFrame("Button", nil, parent)
    btn:SetSize(80, 20)
    btn:SetPoint("LEFT", parent, "LEFT", xOffset, 0)
    
    local bg = btn:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(0.15, 0.15, 0.15, 0.8)
    btn.bg = bg
    
    local text = btn:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    text:SetPoint("CENTER")
    text:SetText(context)
    btn.text = text
    
    btn.context = context
    btn:SetScript("OnClick", function(self)
        selectedContext = self.context
        CatalogUI:UpdateContextButtons()
        CatalogUI:UpdateItemList()
    end)
    
    return btn
end

local function CreateItemRow(parent, item, yOffset)
    local row = CreateFrame("Button", nil, parent)
    row:SetSize(FRAME_WIDTH - 280, ITEM_HEIGHT)
    row:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -yOffset)

    local bg = row:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    local bgAlpha = (yOffset / ITEM_HEIGHT) % 2 == 0 and 0.1 or 0.05
    bg:SetColorTexture(0.2, 0.2, 0.2, bgAlpha)
    row.bg = bg
    row.bgAlpha = bgAlpha

    local glowLeft = row:CreateTexture(nil, "ARTWORK")
    glowLeft:SetSize(3, ITEM_HEIGHT)
    glowLeft:SetPoint("LEFT", row, "LEFT", 0, 0)
    glowLeft:SetColorTexture(1, 0.82, 0, 0)
    row.glowLeft = glowLeft

    local highlight = row:CreateTexture(nil, "HIGHLIGHT")
    highlight:SetAllPoints()
    highlight:SetColorTexture(0.4, 0.4, 0.2, 0.3)

    local xPos = 5

    local indicatorBg = row:CreateTexture(nil, "ARTWORK")
    indicatorBg:SetSize(50, 18)
    indicatorBg:SetPoint("LEFT", row, "LEFT", xPos, 0)
    indicatorBg:SetColorTexture(0, 0, 0, 0.4)
    row.indicatorBg = indicatorBg

    local indicator = row:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    indicator:SetPoint("CENTER", indicatorBg, "CENTER", 0, 0)
    indicator:SetJustifyH("CENTER")

    if item.type == "trinket" then
        local tierColor = TIER_COLORS[item.tier] or TIER_COLORS["D"]
        indicator:SetText(item.tier .. " Tier")
        indicator:SetTextColor(tierColor.r, tierColor.g, tierColor.b)
        indicatorBg:SetColorTexture(tierColor.r * 0.2, tierColor.g * 0.2, tierColor.b * 0.2, 0.6)
    elseif item.type == "bis" then
        indicator:SetText(item.slot or "")
        indicator:SetTextColor(0.9, 0.9, 0.9)
        indicatorBg:SetColorTexture(0.1, 0.1, 0.1, 0.5)
    elseif item.type == "cartel" then
        indicator:SetText(item.details or "Myth")
        indicator:SetTextColor(0.5, 0.8, 1)
        indicatorBg:SetColorTexture(0.1, 0.2, 0.3, 0.6)
    end

    xPos = xPos + 60

    local nameText = row:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    nameText:SetPoint("LEFT", row, "LEFT", xPos, 0)
    nameText:SetWidth(350)
    nameText:SetJustifyH("LEFT")
    nameText:SetText(item.name or "Unknown Item")
    nameText:SetTextColor(1, 1, 1)
    row.nameText = nameText

    row.itemData = item
    row.originalNameColor = {1, 1, 1}

    row:SetScript("OnEnter", function(self)
        self.bg:SetColorTexture(0.3, 0.3, 0.15, 0.8)
        self.glowLeft:SetColorTexture(1, 0.82, 0, 1)
        ShowCustomTooltip(self, self.itemData)
        local itemId = tonumber(self.itemData.id)
        local itemInfo = { GetItemInfo(itemId) }
        if itemInfo[1] then
            local quality = itemInfo[3]
            local r, g, b = GetItemQualityColor(quality)
            self.nameText:SetTextColor(r, g, b)
        end
    end)

    row:SetScript("OnLeave", function(self)
        self.bg:SetColorTexture(0.2, 0.2, 0.2, self.bgAlpha)
        self.glowLeft:SetColorTexture(1, 0.82, 0, 0)
        self.nameText:SetTextColor(1, 1, 1)
        HideCustomTooltip()
    end)

    row:SetScript("OnClick", function(self, button)
        local itemId = tonumber(self.itemData.id)
        if itemId and IsModifiedClick("CHATLINK") then
            local _, link = GetItemInfo(itemId)
            if link then
                ChatEdit_InsertLink(link)
            end
        end
    end)

    return row, yOffset + ITEM_HEIGHT
end

function CatalogUI:UpdateClassButtons()
    if not mainFrame or not mainFrame.classContent then return end
    
    if mainFrame.classContent.children then
        for _, child in ipairs(mainFrame.classContent.children) do
            child:Hide()
            child:ClearAllPoints()
        end
    end
    mainFrame.classContent.children = {}
    
    local yOffset = 5
    local sortedClasses = {}
    
    for classKey, _ in pairs(CLASS_INFO) do
        if TierListAddonData and TierListAddonData[classKey] then
            table.insert(sortedClasses, classKey)
        end
    end
    table.sort(sortedClasses, function(a, b)
        return CLASS_INFO[a].name < CLASS_INFO[b].name
    end)
    
    mainFrame.classButtons = {}
    
    for _, classKey in ipairs(sortedClasses) do
        local btn
        btn, yOffset = CreateClassButton(mainFrame.classContent, classKey, yOffset)
        if btn then
            table.insert(mainFrame.classContent.children, btn)
        end
        
        if selectedClass == classKey then
            btn.bg:SetColorTexture(0.3, 0.3, 0.1, 0.8)
            
            local specs = GetSpecsForClass(classKey)
            for _, specKey in ipairs(specs) do
                local specBtn
                specBtn, yOffset = CreateSpecButton(mainFrame.classContent, specKey, yOffset)
                table.insert(mainFrame.classContent.children, specBtn)
                if specBtn and selectedSpec == specKey then
                    specBtn.selected:Show()
                    specBtn.bg:SetColorTexture(0.2, 0.2, 0.1, 0.8)
                end
            end
            yOffset = yOffset + 5
        end
    end
    
    mainFrame.classContent:SetHeight(yOffset + 20)
end

function CatalogUI:UpdateSpecButtons()
    self:UpdateClassButtons()
end

function CatalogUI:UpdateSourceButtons()
    if not mainFrame or not mainFrame.sourceButtons then return end

    for _, btn in ipairs(mainFrame.sourceButtons) do
        local sourceKey = btn.sourceKey
        local source = nil
        for _, s in ipairs(DATA_SOURCES) do
            if s.key == sourceKey then
                source = s
                break
            end
        end

        if source and source.available then
            if selectedSource == source.key then
                btn.bg:SetColorTexture(source.color[1] * 0.4, source.color[2] * 0.4, source.color[3] * 0.4, 0.9)
                btn.text:SetTextColor(source.color[1], source.color[2], source.color[3])
            else
                btn.bg:SetColorTexture(0.15, 0.15, 0.15, 0.8)
                btn.text:SetTextColor(0.6, 0.6, 0.6)
            end
        end
    end
end

function CatalogUI:UpdateCategoryTabs()
    if not mainFrame or not mainFrame.tabContainer then return end
    
    for _, child in pairs({ mainFrame.tabContainer:GetChildren() }) do
        child:Hide()
        child:SetParent(nil)
    end
    
    if not selectedSpec then return end
    
    local tabs = {
        { key = "bis", name = "Best in Slot" },
        { key = "trinkets", name = "Trinkets" },
        { key = "cartel_chips", name = "Cartel Chips" },
    }
    
    local xOffset = 0
    mainFrame.categoryTabs = {}
    
    for _, tab in ipairs(tabs) do
        local btn = CreateCategoryTab(mainFrame.tabContainer, tab.key, tab.name, xOffset)
        
        if selectedCategory == tab.key then
            btn.bg:SetColorTexture(0.4, 0.35, 0.1, 0.9)
            btn.text:SetTextColor(1, 0.82, 0)
        else
            btn.text:SetTextColor(0.8, 0.8, 0.8)
        end
        
        table.insert(mainFrame.categoryTabs, btn)
        xOffset = xOffset + 110
    end
    
    self:UpdateContextButtons()
end

function CatalogUI:UpdateContextButtons()
    if not mainFrame then return end
    
    if mainFrame.contextButtons then
        for _, btn in ipairs(mainFrame.contextButtons) do
            btn:Hide()
            btn:SetParent(nil)
        end
    end
    mainFrame.contextButtons = {}
    
    if selectedCategory ~= "bis" then
        mainFrame.contextLabel:SetText("")
        return
    end
    
    mainFrame.contextLabel:SetText("Context:")
    
    local contexts = GetAvailableContexts()
    local xOffset = 60
    
    for _, context in ipairs(contexts) do
        local btn = CreateContextButton(mainFrame.rightPanel, context, xOffset)
        btn:SetPoint("LEFT", mainFrame.contextLabel, "LEFT", xOffset, 0)
        
        if selectedContext == context then
            btn.bg:SetColorTexture(0.3, 0.3, 0.1, 0.9)
            btn.text:SetTextColor(1, 0.82, 0)
        else
            btn.text:SetTextColor(0.7, 0.7, 0.7)
        end
        
        table.insert(mainFrame.contextButtons, btn)
        xOffset = xOffset + 90
    end
end

function CatalogUI:UpdateItemList()
    if not mainFrame or not mainFrame.itemContent then return end
    
    if mainFrame.itemContent.children then
        for _, child in ipairs(mainFrame.itemContent.children) do
            if child.Hide then child:Hide() end
            if child.ClearAllPoints then child:ClearAllPoints() end
        end
    end
    mainFrame.itemContent.children = {}
    
    if mainFrame.itemContent.header then
        mainFrame.itemContent.header:SetText("")
    end
    if mainFrame.itemContent.countText then
        mainFrame.itemContent.countText:SetText("")
    end
    
    if not selectedClass or not selectedSpec then
        mainFrame.infoText:Show()
        return
    end
    
    mainFrame.infoText:Hide()
    
    BuildItemList()
    
    local yOffset = 5
    
    if not mainFrame.itemContent.header then
        mainFrame.itemContent.header = mainFrame.itemContent:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    end
    local header = mainFrame.itemContent.header
    header:ClearAllPoints()
    header:SetPoint("TOPLEFT", mainFrame.itemContent, "TOPLEFT", 5, -yOffset)
    
    local classInfo = CLASS_INFO[selectedClass] or { name = selectedClass }
    local specName = SPEC_NAMES[selectedSpec] or selectedSpec
    
    header:SetText(string.format("|cFF%s%s|r - %s", classInfo.color, classInfo.name, specName))
    
    yOffset = yOffset + 30
    
    if not mainFrame.itemContent.countText then
        mainFrame.itemContent.countText = mainFrame.itemContent:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    end
    local countText = mainFrame.itemContent.countText
    countText:ClearAllPoints()
    countText:SetPoint("TOPLEFT", mainFrame.itemContent, "TOPLEFT", 5, -yOffset)
    countText:SetText(string.format("%d items found", #currentItems))
    countText:SetTextColor(0.7, 0.7, 0.7)
    
    yOffset = yOffset + 25
    
    for _, item in ipairs(currentItems) do
        local row
        row, yOffset = CreateItemRow(mainFrame.itemContent, item, yOffset)
        table.insert(mainFrame.itemContent.children, row)
    end
    
    mainFrame.itemContent:SetHeight(yOffset + 50)
end

function CatalogUI:Show()
    if not mainFrame then
        CreateMainFrame()
    end
    
    if not selectedClass and ADDON_NS.WOWRN then
        local playerClass, playerSpec = ADDON_NS.WOWRN:GetPlayerClassSpec()
        if playerClass and TierListAddonData and TierListAddonData[playerClass] then
            selectedClass = playerClass
            if playerSpec and TierListAddonData[playerClass][playerSpec] then
                selectedSpec = playerSpec
            end
        end
    end
    
    self:UpdateClassButtons()
    self:UpdateCategoryTabs()
    self:UpdateItemList()
    
    mainFrame:Show()
end

function CatalogUI:Hide()
    if mainFrame then
        mainFrame:Hide()
    end
end

function CatalogUI:Toggle()
    if mainFrame and mainFrame:IsShown() then
        self:Hide()
    else
        self:Show()
    end
end

function CatalogUI:IsShown()
    return mainFrame and mainFrame:IsShown()
end