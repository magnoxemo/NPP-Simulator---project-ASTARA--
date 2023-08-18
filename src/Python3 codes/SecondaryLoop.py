import CoolProp.CoolProp as CP
import numpy as np

class Turbine():

    def __init__(self,Throttle_valve:object,MoistureSeperator:object
                 ,Reheater:object,HighPressureTurbine:object,LowPressureTurbine:object
                 ):
        self.ThrottleValve=Throttle_valve
        self.MoistureSeperator=MoistureSeperator
        self.Reheater=Reheater
        self.HighPressureTurbine=HighPressureTurbine
        self.LowPressureTurbine=LowPressureTurbine
    
class ThrottleValve():
    def __init__(self,Area_main:float,Area_secondary:float,
                co_efficient_main:float,co_efficient_secondary:float,
                pos_main_valve:float,pos_second_valve:float,enthalpy_at_main_throttle_valve:float):
        
        """ Desgin Parameters  """
        self.A_m=Area_main
        self.A_s=Area_secondary
        self.Cf_m=co_efficient_main
        self.Cf_s=co_efficient_secondary



        self.W_utsg=4*1329.6
        self.SteamTemp=265              #temperature will be in Kelvin
        self.SteamPressure=5e6     
             #pressure will be in Pa
        """ SteamTemp and the SteamPressure will be from the steam generator  
            So once the constructor runs  in the integrator loop I need to update the 
            fluid properties 
            
            Things to keep in mind 
            
            1.Temp will be in Kelvin 
            2.The pressure will be in Pascal

        """
        
        self.h_s=CP.PropSI("H",'T',self.SteamTemp,'P',self.SteamPressure,'water')

        """ control elements """
        if ((pos_main_valve >100 and pos_main_valve<0) or( pos_second_valve>100 and pos_second_valve<0)):
            raise ValueError ("opening percentage of the  Main and secondarythrottle valve must stay in between 0 and 100")
        else:
            self.Pos_main_v=pos_main_valve
            self.pos_second_v=pos_second_valve

        self.Wm=self.Cf_m*self.A_m*self.W_utsg*self.Pos_main_v
        self.W2nd=self.Cf_s*self.A_s*self.W_utsg*self.pos_second_v

        # position of the main and second valve means how much the percentage of the valve is opened 
        #Here is Pos_main_V=100 then it's fully open
        
    def Wmain(self):
        self.Wm=self.Cf_m*self.A_m*self.W_utsg*self.Pos_main_v
        self.W2nd=self.Cf_s*self.A_s*self.W_utsg*self.pos_second_v

class NozzleChest():

    def __init__(self,Effective_volume_of_nozzle_Chest:float,steam_pressure_chest:float,
                 TempatNozzleChest:float,Kc_hp:float,Callender_const1:float,Callender_const2:float):

        """ k1 and k2 are constants in the Callender’s emperical
            equation relating pressure, density and enthalpy of superheated steam

            Kchp is a constant determined at the initial period of the powerplant 
            """
        self.k1=Callender_const1
        self.k2=Callender_const2
        self.Kchp=Kc_hp 

        '''Data loading from the CoolProP'''
        

        self.SteamTemp=265              #temperature will be in Kelvin
        self.SteamPressure=5e6           
        self.h_sd=CP.PropSI("H",'T',self.SteamTemp,'P',self.SteamPressure,'water')
         #enthalpy of the steam drum 

        self.Pc=steam_pressure_chest
        self.SteamTempatChest=TempatNozzleChest
        self.Vc=Effective_volume_of_nozzle_Chest
        self.hc=CP.PropSI("H",'T',self.SteamTempatChest,'P',self.Pc,'water') 
        self.rou_c=CP.PropSI("D",'T',self.SteamTempatChest,'P',self.Pc,'water')
        
        
    def Whp(self,Reheater:object,HighPressureTurbine:object):
        self.Whp1=self.Kchp*np.sqrt(self.Pc*self.rou_c-Reheater.Pressue*HighPressureTurbine.rou_exit)
    
    def P_c(self):
        self.Pc=self.rou_c*(self.k1*self.hc-self.k2)
    
    def Dh_c(self,ThrottleValve:object):
        self.Wmain=ThrottleValve.Wm
        dtdhc=(((self.Wmain*self.h_sd-self.Whp1*self.hc)/(self.rou_c*self.Vc))+\
             (self.Pc/self.rou_c**2)*self.Drou_c())/(1-self.k1)
        
        return dtdhc

    def Drou_c(self,ThrottleValve:object):
        self.Wmain=ThrottleValve.Wm
        dtdrou_c=(self.Wmain-self.Whp1)/self.Vc
        return dtdrou_c
    
    ''' As we can get the transient feed back of the enthalpy and pressure and density 
    we can find out the temperature of the steam using cool prop properties '''
    


class MoistureSeperator():
    def __init__(self,enthalpy_hpex:float,flow_rate_of_the_steam_from_the_steamseperator:float,
                 Temperature:float):
                
        
        #

        self.Whpex=flow_rate_of_the_steam_from_the_steamseperator
        self.Temp=Temperature
        self.h_hpex=enthalpy_hpex
        self.hf=CP.PropsSI("H",'T',self.Temp,'Q',0,'water')
        self.hg=CP.PropsSI("H",'T',self.Temp,'Q',1,'water')
        self.hfg=self.hg-self.hf

        #variable
        self.W_mss=(self.h_hpex-self.hf)*self.Whpex/(self.hfg)

    def Wmsw(self,HighPressureTurbine:object,NozzleChest:object):
        self.Wbhp=HighPressureTurbine.Wbhp
        self.Whp1=NozzleChest.Whp()
        self.W_msw=(self.W_hp1-self.Wbhp)-((self.h_hpex-self.hf)*self.Whpex/(self.hfg))
        
    def Wmss(self):
        self.W_mss=(self.h_hpex-self.hf)*self.Whpex/(self.hfg)  #that will go to the reheater 

        '''there are no differential eq in the MoistureSeperator 
         
          bug fixing done to this one '''


class Reheater():

    class Reheater_steam():
        def __init__(self,pressure:float,time_const_flowrate:float,time_const_heating:float,
                    flow_rate_to_2nd_heater:float,steam_temp:float,Heater_temp:float,
                    Heat:float,heat_transfer_coefficient:float,Gas_const:float):
            self.Pressue=pressure
            self.w_2nd=ThrottleValve.W_2nd
            self.tau_1=time_const_flowrate
            self.tau_2=time_const_heating
            self.W_ro=flow_rate_to_2nd_heater #for initial_cond
            self.T_steam=steam_temp
            self.T_r=Heater_temp
            self.Q=Heat
            self.H=heat_transfer_coefficient
            self.R=Gas_const

        def _dwro(self):

            Dwro=(self.w_2nd-self.W_ro)/self.tau_1

            return Dwro
        
        def _dQr(self):

            dQr=((self.T_steam-self.T_r)*(self.w_2nd+self.W_ro)*self.H-2*self.Q)/(2*self.tau_2)
            self.T_r=self.P/(self.R*self.rou_r)

            return dQr
        
    class MainSteam():
        def __init__(self):
            pass

class HighPressureTurbine():
    def __init__(self,exit_steam_density:float,inlet_flow_rate:float,
                 exit_flow_rate_to_MS:float,exit_flow_rate_to_heater:float,
                 time_const:float,HP_co_efficient:float) :
        
        self.rou_exit=exit_steam_density
        self.Whpex=exit_flow_rate_to_MS
        self.Wbhp=exit_flow_rate_to_heater
        self.Tau=time_const
        self.Whp_in=inlet_flow_rate
        self.C=HP_co_efficient

    def DWhpex(self):

        dtdWhpex=((self.Whp_in-self.W_bhp)-self.W_hpex)/self.Tau

        return dtdWhpex
    
    def _wbhp(self):

        self.wbhp=self.C*self.Whp_in
         
    

class LowPressureTurbine():
    def __init__(self,exit_steam_density:float,inlet_flow_rate:float,
                 exit_flow_rate_to_MS:float,exit_flow_rate_to_heater:float,
                 time_const:float,LP_co_efficient:float) :
        
        self.rou_exit=exit_steam_density
        self.W_lpex=exit_flow_rate_to_MS    #goes to the condenser 
        self.W_blp=exit_flow_rate_to_heater #goes to the heater 
        self.Tau=time_const
        self.Wlp_in=inlet_flow_rate         #this comes from the moisture seperator and reheater
        self.C=LP_co_efficient
    
    def _dwhpex(self):

        Dwlpex=((self.Wlp_in-self.W_blp)-self.W_lpex)/self.Tau

        return Dwlpex
    
    def _wbhp(self):

        self.wbhp=self.C*self.Wlp_in
