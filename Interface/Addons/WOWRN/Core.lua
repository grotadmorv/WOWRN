local ADDON_NAME, ADDON_NS = ...

local WOWRN = {}
ADDON_NS.WOWRN = WOWRN

local CLASS_NAME_MAP = {
    ["DEATHKNIGHT"] = "death-knight",
    ["DEMONHUNTER"] = "demon-hunter",
    ["DRUID"] = "druid",
    ["EVOKER"] = "evoker",
    ["HUNTER"] = "hunter",
    ["MAGE"] = "mage",
    ["MONK"] = "monk",
    ["PALADIN"] = "paladin",
    ["PRIEST"] = "priest",
    ["ROGUE"] = "rogue",
    ["SHAMAN"] = "shaman",
    ["WARLOCK"] = "warlock",
    ["WARRIOR"] = "warrior",
}

local SPEC_NAME_MAP = {
    -- Death Knight
    [250] = "blood",
    [251] = "frost",
    [252] = "unholy",
    -- Demon Hunter
    [577] = "havoc",
    [581] = "vengeance",
    [582] = "devourer",
    -- Druid
    [102] = "balance",
    [103] = "feral",
    [104] = "guardian",
    [105] = "restoration",
    -- Evoker
    [1467] = "devastation",
    [1468] = "preservation",
    [1473] = "augmentation",
    -- Hunter
    [253] = "beast-mastery",
    [254] = "marksmanship",
    [255] = "survival",
    -- Mage
    [62] = "arcane",
    [63] = "fire",
    [64] = "frost",
    -- Monk
    [268] = "brewmaster",
    [270] = "mistweaver",
    [269] = "windwalker",
    -- Paladin
    [65] = "holy",
    [66] = "protection",
    [70] = "retribution",
    -- Priest
    [256] = "discipline",
    [257] = "holy",
    [258] = "shadow",
    -- Rogue
    [259] = "assassination",
    [260] = "outlaw",
    [261] = "subtlety",
    -- Shaman
    [262] = "elemental",
    [263] = "enhancement",
    [264] = "restoration",
    -- Warlock
    [265] = "affliction",
    [266] = "demonology",
    [267] = "destruction",
    -- Warrior
    [71] = "arms",
    [72] = "fury",
    [73] = "protection",
}

local BIS_COLOR = "|cFF00FF00"
local TIER_COLORS = {
    ["S"] = "|cFFFF8000",
    ["A"] = "|cFFA335EE",
    ["B"] = "|cFF0070DD",
    ["C"] = "|cFF1EFF00",
    ["D"] = "|cFFFFFFFF",
    ["F"] = "|cFF9D9D9D",
}

local playerClass = nil
local playerSpec = nil

function WOWRN:GetPlayerClassSpec()
    local _, classToken = UnitClass("player")
    playerClass = CLASS_NAME_MAP[classToken]

    local specIndex = GetSpecialization()
    if specIndex then
        local specID = GetSpecializationInfo(specIndex)
        playerSpec = SPEC_NAME_MAP[specID]
    end

    return playerClass, playerSpec
end

function WOWRN:GetBisInfo(itemId)
    if not TierListAddonData or not playerClass or not playerSpec then
        return nil
    end

    local classData = TierListAddonData[playerClass]
    if not classData then return nil end

    local specData = classData[playerSpec]
    if not specData then return nil end

    local bisInfo = {}

    if specData.bis then
        for context, items in pairs(specData.bis) do
            for _, item in ipairs(items) do
                if item.id == itemId then
                    table.insert(bisInfo, {
                        type = "bis",
                        context = context,
                        slot = item.slot,
                        source_type = item.source_type,
                        boss_name = item.boss_name,
                        location_name = item.location_name,
                    })
                end
            end
        end
    end

    if specData.trinkets then
        for tier, items in pairs(specData.trinkets) do
            for _, item in ipairs(items) do
                if item.id == itemId then
                    table.insert(bisInfo, {
                        type = "trinket",
                        tier = tier,
                        source_type = item.source_type,
                        boss_name = item.boss_name,
                        location_name = item.location_name,
                    })
                end
            end
        end
    end
    
    if specData.cartel_chips then
        for _, item in ipairs(specData.cartel_chips) do
            if item.id == itemId then
                table.insert(bisInfo, {
                    type = "cartel",
                    details = item.details,
                })
            end
        end
    end

    return #bisInfo > 0 and bisInfo or nil
end

function WOWRN:AddTooltipLine(tooltip, itemId)
    local bisInfo = self:GetBisInfo(itemId)
    if not bisInfo then return end

    tooltip:AddLine(" ")
    tooltip:AddLine("|cFFFFD700[WOWRN]|r BiS Info:")

    for _, info in ipairs(bisInfo) do
        if info.type == "bis" then
            local text = string.format(
                "  %sBiS|r for %s (%s)",
                BIS_COLOR,
                info.context,
                info.slot
            )
            tooltip:AddLine(text)
            
            if info.source_type then
                local dropText = self:GetDropLocationText(info.source_type, info.boss_name, info.location_name)
                if dropText then
                    tooltip:AddLine("    " .. dropText)
                end
            end
        elseif info.type == "trinket" then
            local tierColor = TIER_COLORS[info.tier] or "|cFFFFFFFF"
            local text = string.format(
                "  Trinket Tier: %s%s|r",
                tierColor,
                info.tier
            )
            tooltip:AddLine(text)
            
            if info.source_type then
                local dropText = self:GetDropLocationText(info.source_type, info.boss_name, info.location_name)
                if dropText then
                    tooltip:AddLine("    " .. dropText)
                end
            end
        elseif info.type == "cartel" then
            local text = string.format(
                "  |cFF00CCFFCartel Chip|r %s",
                info.details or ""
            )
            tooltip:AddLine(text)
        end
    end
end

function WOWRN:GetDropLocationText(sourceType, bossName, locationName)
    if sourceType == "quest, vendor or crafted" then
        return "|cFFFF8000Quest vendor or crafted Item|r"
    elseif bossName and locationName then
        return string.format("|cFF9D9D9DDropped by: %s - %s|r", bossName, locationName)
    else
        return nil
    end
end

local function OnTooltipSetItem(tooltip)
    if not tooltip or tooltip:IsForbidden() then return end
    if WOWRNSettings and WOWRNSettings.enableTooltips == false then return end
    if not tooltip.GetItem then return end

    local _, itemLink = tooltip:GetItem()
    if not itemLink then return end

    local itemId = GetItemInfoInstant(itemLink)
    if not itemId then return end

    WOWRN:AddTooltipLine(tooltip, tostring(itemId))
end

local function HandleSlashCommand(msg)
    local cmd = msg:lower():trim()
    
    if cmd == "" or cmd == "show" or cmd == "catalog" then
        if ADDON_NS.CatalogUI then
            ADDON_NS.CatalogUI:Toggle()
        end
    elseif cmd == "minimap" then
        if ADDON_NS.MinimapButton then
            ADDON_NS.MinimapButton:Toggle()
            if ADDON_NS.MinimapButton:IsShown() then
                print("|cFFFFD700[WOWRN]|r Minimap button shown")
            else
                print("|cFFFFD700[WOWRN]|r Minimap button hidden")
            end
        end
    elseif cmd == "help" then
        print("|cFFFFD700[WOWRN]|r Commands:")
        print("  |cFF00FF00/wowrn|r - Open the tier list catalog")
        print("  |cFF00FF00/wowrn catalog|r - Open the tier list catalog")
        print("  |cFF00FF00/wowrn minimap|r - Toggle minimap button")
        print("  |cFF00FF00/wowrn help|r - Show this help message")
    elseif cmd == "options" or cmd == "config" then
        if ADDON_NS.Options then
            ADDON_NS.Options:Open()
        end
    else
        print("|cFFFFD700[WOWRN]|r Unknown command: " .. cmd)
        print("  Type |cFF00FF00/wowrn help|r for available commands")
    end
end

SLASH_WOWRN1 = "/wowrn"
SLASH_WOWRN2 = "/rn"
SlashCmdList["WOWRN"] = HandleSlashCommand

local function OnPlayerLogin()
    WOWRN:GetPlayerClassSpec()
    WOWRNSettings = WOWRNSettings or {}
    WOWRNSettings.enableTooltips = WOWRNSettings.enableTooltips ~= false
    if ADDON_NS.MinimapButton then
        ADDON_NS.MinimapButton:Create()
    end
    if ADDON_NS.Options then
        ADDON_NS.Options:Initialize()
    end
    print("|cFFFFD700[WOWRN]|r Loaded! Type |cFF00FF00/wowrn|r to open the catalog")
end

local function OnSpecChange()
    WOWRN:GetPlayerClassSpec()
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_SPECIALIZATION_CHANGED")
frame:SetScript("OnEvent", function(self, event, ...)
    if event == "PLAYER_LOGIN" then
        OnPlayerLogin()
    elseif event == "PLAYER_SPECIALIZATION_CHANGED" then
        OnSpecChange()
    end
end)

if TooltipDataProcessor then
    TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Item, OnTooltipSetItem)
else
    GameTooltip:HookScript("OnTooltipSetItem", OnTooltipSetItem)
end
