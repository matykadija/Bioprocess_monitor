import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

class BioprocessMonitor:
    def __init__(self, filepath, ph_lims, temperature_lims):
        """
        Utility class used to monitor bioprocesses by
        generating dashboards and summaries.

        Parameters
        ----------
        filepath : str
            Input CSV dataset path.
        ph_lims : tuple[float, float]
            Lower and upper acceptable pH limits.
        temperature_lims : tuple[float, float]
            Lower and upper acceptable temperature limits.
        """
        self.df = pd.read_csv(filepath)
        self.ph_lims = ph_lims
        self.temperature_lims = temperature_lims

        #le code lis le fichier csv, le garde en memoire dans le self.df. On met self. permet aux autres methodes de reutiliser les infos.


    def extract_batch(self, batch_id):
        """
        Extracts data corresponding to a single batch.

        Parameters
        ----------
        batch_id : int
            Batch identifier.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing only rows associated with
            the requested batch.
        """
        return self.df[self.df["batch_id"] == batch_id]

    def optimal_ph_mask(self, df_batch):
        """
        Determines whether each pH measurement falls within
        the acceptable operating range.

        Parameters
        ----------
        df_batch : pandas.DataFrame
            Batch-specific DataFrame.

        Returns
        -------
        array-like of bool
            A mask whereby True indicates that the measurement
            is within the acceptable operating range.
        """
        return df_batch["pH"].between(self.ph_lims[0], self.ph_lims[1])


    def optimal_temperature_mask(self, df_batch):
        """
        Determines whether each temperature measurement falls
        within the acceptable operating range.

        Parameters
        ----------
        df_batch : pandas.DataFrame
            Batch-specific DataFrame.

        Returns
        -------
        array-like of bool
            A mask whereby True indicates that the measurement
            is within the acceptable operating range.
        """
        return df_batch["temperature_C"].between(self.temperature_lims[0], self.temperature_lims[1])

    def get_n_batches(self):
        """
        Determines the number of unique batches present
        in the dataset.

        Returns
        -------
        int
            Total number of distinct batch identifiers.
        """

        return self.df["batch_id"].nunique()
    


    def export_dashboard(self, batch_id, filepath):
        """
        Creates and saves a dashboard figure for a single batch.

        Parameters
        ----------
        batch_id : int
            Batch identifier.
        filepath : str
            Output PNG image path.

        Dashboard Requirements
        ----------------------
        Create a 2 × 2 figure containing:

        Top-Left
            Glucose, biomass, and product concentrations versus time.
            - A different color and marker should be used for each substance.

        Top-Right
            Temperature versus time.
            - Measurements within the acceptable temperature range
              should be displayed as green circles.
            - Measurements outside the acceptable temperature range
              should be displayed as red X markers.

        Bottom-Left
            pH versus time.
            - Measurements within the acceptable pH range
              should be displayed as green circles.
            - Measurements outside the acceptable pH range
              should be displayed as red X markers.

        Bottom-Right
            Dissolved oxygen versus time.

        Additional Requirements
        -----------------------
        - Use scatter plots.
        - Add x-axis and y-axis labels.
        - Add legends where appropriate.
        - Apply consistent formatting across all subplots unless
          indicated otherwise.
        - Apply a tick spacing of 6 h on the x-axis for all subplots.
        - Save the figure to the provided filepath.
        - Close the figure after saving.
        """

        df_batch = self.extract_batch(batch_id)

        fig, axs = plt.subplots(2, 2, figsize = (12, 9))  #2x2

        #o2 dissous
        ax = axs[1, 1] #designe une case
        ax.scatter(df_batch["time_h"], df_batch["DO_percent"])
        ax.set_xlabel("Time (h)") #ajoute les noms des axes
        ax.set_ylabel("Dissolved oxygen (%)")


        #ph
        ax = axs[1, 0]
        mask_ph = self.optimal_ph_mask(df_batch)
        ax.scatter(df_batch["time_h"][mask_ph], df_batch["pH"][mask_ph],
                   color = "green", marker="o", label="Within range")
        ax.scatter(df_batch["time_h"][~mask_ph], df_batch["pH"][~mask_ph],
                   color = "red", marker="x", label="Outside range")
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("pH")
        ax.legend()

        #temperature
        ax = axs[0, 1]
        mask_temperature = self.optimal_temperature_mask(df_batch)
        ax.scatter(df_batch["time_h"][mask_temperature], df_batch["temperature_C"][mask_temperature],
                   color = "green", marker="o", label="Within range")
        ax.scatter(df_batch["time_h"][~mask_temperature], df_batch["temperature_C"][~mask_temperature],
                   color = "red", marker="x", label="Outside range")
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("Temperature (Celsius)")
        ax.legend()

        #concentrations
        ax = axs[0, 0]
        ax.scatter(df_batch["time_h"], df_batch["C_glucose_g_L^-1"],
                   color = "blue", marker="o", label="Glucose")
        ax.scatter(df_batch["time_h"], df_batch["C_biomass_g_L^-1"],
                   color="yellow", marker="s", label="Biomass")
        ax.scatter(df_batch["time_h"], df_batch["C_product_g_L^-1"],
                   color="purple", marker="^", label="Product")
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("Concentration (g/L)")
        ax.legend()

        for ax in axs.flat:
            ax.xaxis.set_major_locator(MultipleLocator(6))

        fig.suptitle(f"Batch {batch_id}") #titre fig
        fig.tight_layout()

        fig.savefig(filepath)
        plt.close(fig)


    def export_summary(self, filepath):
        """
        Generates a batch summary table and exports it to a CSV file.

        Parameters
        ----------
        filepath : str
            Output CSV table path.

        Summary Table Columns
        ---------------------
        batch_id
            Batch identifier.

        ph_optimal_percent
            Percentage of measurements in a batch within the
            acceptable pH range, rounded to 2 decimal places.

        temperature_optimal_percent
            Percentage of measurements in a batch within the
            acceptable temperature range, rounded to 2 decimal places.

        C_product_g_L^-1_final
            Final product concentration for the batch.
        """



        rows = [] #liste qui va recevoir une ligne par batch

        for batch_id in range(1, self.get_n_batches() +1):
            df_batch = self.extract_batch(batch_id)

            row = {
                "batch_id": batch_id,
                "ph_optimal_percent": round(self.optimal_ph_mask(df_batch).mean()*100,2),
                "temperature_optimal_percent": round(self.optimal_temperature_mask(df_batch).mean()*100,2),
                "C_product_g_L^-1_final":df_batch["C_product_g_L^-1"].iloc[-1],
            }
            rows.append(row)   #pour ajouter la ligne a la liste

        pd.DataFrame(rows).to_csv(filepath, index=False) #transformer en tableau et sauvergarder
