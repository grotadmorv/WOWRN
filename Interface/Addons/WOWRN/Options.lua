local ADDON_NAME, ADDON_NS = ...

local Options = {}
ADDON_NS.Options = Options

local function CreateOptionsPanel()
    local panel = CreateFrame("Frame")
    panel.name = "WOWRN"
    local title = panel:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", 16, -16)
    title:SetText("|cFFFFD700WOWRN|r - BiS & Tier List")
    local desc = panel:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    desc:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -8)
    desc:SetText("Displays Best-in-Slot and Tier List information on item tooltips.")
    desc:SetJustifyH("LEFT")
    local yOffset = -70
    local enableTooltips = CreateFrame("CheckButton", "WOWRNOptionEnableTooltips", panel, "InterfaceOptionsCheckButtonTemplate")
    enableTooltips:SetPoint("TOPLEFT", 16, yOffset)
    enableTooltips.Text:SetText("Enable BiS info in tooltips")
    enableTooltips:SetChecked(WOWRNSettings.enableTooltips ~= false)
    enableTooltips:SetScript("OnClick", function(self)
        WOWRNSettings.enableTooltips = self:GetChecked()
    end)
    
    yOffset = yOffset - 30
    local showMinimap = CreateFrame("CheckButton", "WOWRNOptionShowMinimap", panel, "InterfaceOptionsCheckButtonTemplate")
    showMinimap:SetPoint("TOPLEFT", 16, yOffset)
    showMinimap.Text:SetText("Show minimap button")
    showMinimap:SetChecked(not (WOWRNSettings.minimap and WOWRNSettings.minimap.hide))
    showMinimap:SetScript("OnClick", function(self)
        if self:GetChecked() then
            ADDON_NS.MinimapButton:Show()
        else
            ADDON_NS.MinimapButton:Hide()
        end
    end)
    
    yOffset = yOffset - 40
    local openCatalog = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    openCatalog:SetPoint("TOPLEFT", 16, yOffset)
    openCatalog:SetSize(200, 25)
    openCatalog:SetText("Open Catalog")
    openCatalog:SetScript("OnClick", function()
        ADDON_NS.CatalogUI:Show()
    end)
    
    yOffset = yOffset - 50
    local version = panel:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    version:SetPoint("TOPLEFT", 16, yOffset)
    version:SetText("|cFF888888Version 1.0.0 | By Sahra Vadrot|r")
    yOffset = yOffset - 20
    local commands = panel:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    commands:SetPoint("TOPLEFT", 16, yOffset)
    commands:SetText("Commands:")
    yOffset = yOffset - 18
    local cmdList = panel:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    cmdList:SetPoint("TOPLEFT", 16, yOffset)
    cmdList:SetText("|cFF00FF00/wowrn|r - Open the catalog\n|cFF00FF00/wowrn minimap|r - Show/hide the minimap button\n|cFF00FF00/wowrn help|r - Help")
    cmdList:SetJustifyH("LEFT")
    return panel
end

function Options:Initialize()
    local panel = CreateOptionsPanel()
    if Settings and Settings.RegisterCanvasLayoutCategory then
        local category = Settings.RegisterCanvasLayoutCategory(panel, panel.name)
        Settings.RegisterAddOnCategory(category)
        Options.categoryID = category:GetID()
    else
        InterfaceOptions_AddCategory(panel)
    end
    
    Options.panel = panel
end

function Options:Open()
    if Settings and Settings.OpenToCategory then
        Settings.OpenToCategory(Options.categoryID or "WOWRN")
    else
        InterfaceOptionsFrame_OpenToCategory("WOWRN")
        InterfaceOptionsFrame_OpenToCategory("WOWRN")
    end
end