local ADDON_NAME, ADDON_NS = ...
local MinimapButton = {}
ADDON_NS.MinimapButton = MinimapButton

local BUTTON_NAME = "WOWRNMinimapButton"
local ICON_PATH = "Interface\\AddOns\\WOWRN\\Textures\\wowrn-logo"
local FALLBACK_ICON = "Interface\\Icons\\INV_Misc_Book_09"

local defaultPosition = {
    minimapPos = 220,
    hide = false,
}

local button = nil
local isDragging = false

local function UpdatePosition()
    if not button then return end
    
    local angle = math.rad(WOWRNSettings.minimap.minimapPos or defaultPosition.minimapPos)
    local radius = 102
    
    local x = math.cos(angle) * radius
    local y = math.sin(angle) * radius
    
    button:ClearAllPoints()
    button:SetPoint("CENTER", Minimap, "CENTER", x, y)
end

local function OnDragStart(self)
    isDragging = true
    self:LockHighlight()
end

local function OnDragStop(self)
    isDragging = false
    self:UnlockHighlight()
    
    local mx, my = Minimap:GetCenter()
    local px, py = GetCursorPosition()
    local scale = Minimap:GetEffectiveScale()
    
    px, py = px / scale, py / scale
    
    local angle = math.deg(math.atan2(py - my, px - mx))
    WOWRNSettings.minimap.minimapPos = angle
    
    UpdatePosition()
end

local function OnUpdate(self)
    if isDragging then
        local mx, my = Minimap:GetCenter()
        local px, py = GetCursorPosition()
        local scale = Minimap:GetEffectiveScale()
        
        px, py = px / scale, py / scale
        
        local angle = math.deg(math.atan2(py - my, px - mx))
        WOWRNSettings.minimap.minimapPos = angle
        
        UpdatePosition()
    end
end

local function OnClick(self, buttonType)
    if buttonType == "LeftButton" then
        if ADDON_NS.CatalogUI then
            ADDON_NS.CatalogUI:Toggle()
        end
    elseif buttonType == "RightButton" then
        print("|cFFFFD700[WOWRN]|r Right-click for options coming soon!")
        print("|cFFFFD700[WOWRN]|r Use |cFF00FF00/wowrn|r to open the catalog")
    end
end

local function OnEnter(self)
    GameTooltip:SetOwner(self, "ANCHOR_LEFT")
    GameTooltip:ClearLines()
    GameTooltip:AddLine("|cFFFFD700WOWRN|r - BiS & Tier List", 1, 1, 1)
    GameTooltip:AddLine(" ")
    GameTooltip:AddLine("|cFF00FF00Left-Click:|r Open Catalog", 0.8, 0.8, 0.8)
    GameTooltip:AddLine("|cFF00FF00Right-Click:|r Options", 0.8, 0.8, 0.8)
    GameTooltip:AddLine("|cFF00FF00Drag:|r Move button", 0.8, 0.8, 0.8)
    GameTooltip:Show()
end

local function OnLeave(self)
    GameTooltip:Hide()
end

function MinimapButton:Create()
    if button then return end
    
    WOWRNSettings = WOWRNSettings or {}
    WOWRNSettings.minimap = WOWRNSettings.minimap or {}
    
    for k, v in pairs(defaultPosition) do
        if WOWRNSettings.minimap[k] == nil then
            WOWRNSettings.minimap[k] = v
        end
    end
    
    button = CreateFrame("Button", BUTTON_NAME, Minimap)
    button:SetSize(32, 32)
    button:SetFrameStrata("MEDIUM")
    button:SetFrameLevel(8)
    
    button:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
    
    local overlay = button:CreateTexture(nil, "OVERLAY")
    overlay:SetSize(53, 53)
    overlay:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")
    overlay:SetPoint("TOPLEFT", button, "TOPLEFT", 0, 0)
    
    local icon = button:CreateTexture(nil, "BACKGROUND")
    icon:SetSize(20, 20)
    icon:SetPoint("CENTER", button, "CENTER", 0, 0)
    
    icon:SetTexture(ICON_PATH)
    if not icon:GetTexture() then
        icon:SetTexture(FALLBACK_ICON)
    end
    
    button.icon = icon
    
    button:SetMovable(true)
    button:EnableMouse(true)
    button:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    button:RegisterForDrag("LeftButton")
    button:SetScript("OnDragStart", OnDragStart)
    button:SetScript("OnDragStop", OnDragStop)
    button:SetScript("OnUpdate", OnUpdate)
    button:SetScript("OnClick", OnClick)
    button:SetScript("OnEnter", OnEnter)
    button:SetScript("OnLeave", OnLeave)
    
    UpdatePosition()
    
    if WOWRNSettings.minimap.hide then
        button:Hide()
    else
        button:Show()
    end
end

function MinimapButton:Show()
    if button then
        button:Show()
        WOWRNSettings.minimap.hide = false
    end
end

function MinimapButton:Hide()
    if button then
        button:Hide()
        WOWRNSettings.minimap.hide = true
    end
end

function MinimapButton:Toggle()
    if button then
        if button:IsShown() then
            self:Hide()
        else
            self:Show()
        end
    end
end

function MinimapButton:IsShown()
    return button and button:IsShown()
end