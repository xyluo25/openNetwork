# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, March 9th 2023
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################


import pandas as pd
import json
from pathlib import Path
import os
from typing import Union
from collections import ChainMap


class OSM_RelationID_Finder:
    """A class to find the osm relation id of a city globally
    """

    def __init__(self):

        # the default path to save/load the global relation id
        self.path_osm_relation_id = self.path2linux(os.path.join(
            Path(__file__).resolve().parent, "datasets/g_osm_relation_id.json"))

        # load the global relation id
        try:
            self._init_osm_relation_id()
        except FileNotFoundError as e:
            print(e)

    def _init_osm_relation_id(self) -> None:
        """A function tool to read the global city relation id

        Returns:
            dict: a dictionary of global city relation id
        """

        with open(self.path_osm_relation_id, "r") as f:
            self.g_osm_relation_id = json.load(f)

    @property
    def available_country(self) -> list:
        """A function tool to find the osm relation id of a city globally

        Returns:
            list: a list of osm relation id

        Example:
            >>> from osm2gmns import OSM_RelationID_Finder
            >>> finder = OSM_RelationID_Finder()
            >>> finder.available_country
            ["United States", "China"]
        """
        return list(self.g_osm_relation_id.keys())

    def read_country_rid(self, path_country_city: str) -> dict:
        """A function to read cities relation id from a csv file

        Args:
            path_country_city (str): a civ file with columns: country_name, state_name, city_name, city_id, state_id

        Returns:
            dict: a dictionary contains cities relation id of a country

        Example:
            >>> from osm2gmns import OSM_RelationID_Finder
            >>> finder = OSM_RelationID_Finder()
            >>> finder.read_country_rid("datasets/country_city_relation_id.csv")
            {"United States": {"California": {"Los Angeles": 123456, "San Francisco": 123457, "California_state": ""}, "New York": {"New York": 123458, "New York_state": ""}}
        """

        # read the country based city data
        df_country_single = pd.read_csv(path_country_city)

        # get the country name from the input dataframe
        country_name = df_country_single["country_name"].unique()[0]
        states_name = [
            i for i in df_country_single["state_name"].unique().tolist() if str(i) != 'nan']

        # get the state names from the input dataframe
        country_rid_dict = {}

        # prepare each state value
        for state in states_name:
            # get cities in each state
            df_state_single = df_country_single[df_country_single['state_name'] == state]

            # get the city names and relation id from the input dataframe
            country_rid_dict[state.lower()] = dict(zip(df_state_single['city_name'].apply(
                lambda x: x.lower()), df_state_single['city_id']))

            # add state name and relation to the dictionary
            country_rid_dict[state.lower()][f"{state.lower()}_state"] = ""
        print(f"the country {country_name} is read.")
        return {country_name.lower(): country_rid_dict}

    def update_country(self, path_country: str) -> None:
        """A function to update the relation id of a country in g_osm_relation_id

        Args:
            path_country (str): a csv file with columns: country_name, state_name, city_name, city_id, state_id

        Examples:
            >>> from osm2gmns import OSM_RelationID_Finder
            >>> finder = OSM_RelationID_Finder()
            >>> finder.update_country("datasets/country_city_relation_id.csv")
            "the country XX is updated."
        """
        country_dict = self.read_country_rid(path_country)
        self.g_osm_relation_id = {**self.g_osm_relation_id, **country_dict}
        self._dict2json(self.g_osm_relation_id, self.path_osm_relation_id)
        print(f"the country {country_dict.keys()} is updated.")

    def _dict2json(self, data: dict, filename: str = "data.json"):
        """A function tool to save data to json file

        Args:
            data (dict): the data to be saved
            filename (str): the path to save the data
        """
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    # convert OS path to standard linux path
    def path2linux(self, path: Union[str, Path]) -> str:
        """Convert a path to a linux path, linux path can run in windows, linux and mac"""
        try:
            return path.replace("\\", "/")
        except Exception:
            return str(path).replace("\\", "/")

    def find_osm_relation_id(self, name: str, country: str = "united states", state: str = None) -> str:
        """A function to find the osm relation id of a city globally

        Args:
            name (str): city or state name
            country (str, optional): a country name. Defaults to "united states".
            state (str, optional): the state name under a country. Defaults to None.

        Raises:
            ValueError: city or state name is not provided
            ValueError: country is not found/provided in g_osm_relation_id
            ValueError: state is not found/provided in a country
            ValueError: city is not found

        Returns:
            str: the osm relation id of a city

        Examples:
            >>> from osm2gmns import OSM_RelationID_Finder
            >>> finder = OSM_RelationID_Finder()

            #### successfully find the relation id of a city ####
            >>> finder.find_osm_relation_id("Los Angeles", "United States", "California")

            #### not provide city name ####
            >>> finder.find_osm_relation_id("", "United States", "California")
            ValueError: the city name is not provided

            #### country name not found ####
            >>> finder.find_osm_relation_id("Los Angeles", "US", "California")
            ValueError: the country US is not found in the database, you can find the available country by calling the function available_country

            #### state name not found ####
            >>> finder.find_osm_relation_id("Los Angeles", "United States", "CA")
            ValueError: the state CA is not found in the country United States.
        """

        # if name not provide, raise error
        if not name:
            raise ValueError("the city name is not provided")

        # Step 1 find and check the country
        if country.lower() not in self.g_osm_relation_id:
            raise ValueError(
                f"the country {country} is not found in the database, you can find the available country by calling the function available_country")

        # Step 2 find and check the state
        if state:
            # check if the state is in the country
            if state.lower() not in self.g_osm_relation_id[country.lower()]:
                # if state is not in the country, check if state start with the the state name
                start_with_state = [i for i in self.g_osm_relation_id[country.lower()].keys(
                ) if i.startswith(state.lower())]

                # if start with state is found, use the start with state
                if not start_with_state:
                    raise ValueError(
                        f"the state {state} is not found in the country {country}")

                print(
                    f"the state {state} is not found in the {country}, but states start with {state} is found: \n")
                for i in start_with_state:
                    print(i)
                return None
        else:
            print(
                f"State not provided, we will search city name in all states in the country {country}\n")

        # Step 3 find the city

        # state not provided
        if not state:
            # get all cities in the country
            states_dict_list = [self.g_osm_relation_id[country.lower(
            )][i] for i in self.g_osm_relation_id[country.lower()].keys()]
            cites_dict = dict(ChainMap(*states_dict_list))
        else:
            # get all cities in the state
            cites_dict = self.g_osm_relation_id[country.lower()][state.lower()]

        if name.lower() in cites_dict:
            return f"Relation id: {name}: {cites_dict[name.lower()]}"

        start_with_city = [
            i for i in cites_dict.keys() if i.startswith(name.lower())]

        if not start_with_city:
            raise ValueError(
                f"the city {name} is not found, please check the city name")

        print(
            f"The city {name} is not found, but cities start with {name} is found: \n")
        for i in start_with_city:
            print(f"{i}: {cites_dict[i]}")


if __name__ == "__main__":

    path_country_city = r"C:\Users\roche\Anaconda_workspace\001_Github\openNetwork\docs\us_cities_7824.csv"

    path_china = r"C:\Users\roche\Anaconda_workspace\001_Github\openNetwork\docs\cities_china_1545.csv"

    finder = OSM_RelationID_Finder()
    # print(finder.available_country)
    # print(finder.g_osm_relation_id)
