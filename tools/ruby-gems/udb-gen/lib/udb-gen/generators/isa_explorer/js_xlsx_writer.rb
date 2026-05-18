# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"
require "write_xlsx"

module UdbGen
  module IsaExplorer
    class JsXlsxWriter
      extend T::Sig

      # Create ISA Explorer table as JavaScript file.
      #
      # @param table Table data
      # @param div_name Name of div element in HTML
      sig { params(table: T::Hash[String, T::Array[T.untyped]], div_name: String).returns(String) }
      def js_table(table, div_name)
        columns = table.fetch("columns")
        rows = table.fetch("rows")

        fp = StringIO.new
        fp.write "// Define data array\n"
        fp.write "\n"
        fp.write "var tabledata = [\n"

        rows.each do |row|
          items = []
          columns.each_index do |i|
            column = columns.fetch(i)
            column_name = column.fetch(:name).gsub("\n", " ")
            cell = row.fetch(i)
            if cell.is_a?(String)
              cell_fmt = '"' + row.fetch(i).gsub("\n", "\\n") + '"'
            elsif cell.is_a?(TrueClass) || cell.is_a?(FalseClass) || cell.is_a?(Integer)
              cell_fmt = "#{cell}"
            elsif cell.is_a?(Array)
              cell_fmt = '"' + cell.join("\\n") + '"'
            else
              raise ArgumentError, "Unknown cell class of #{cell.class} for '#{cell}'"
            end
            items.append('"' + column_name + '":' + cell_fmt)
          end
          fp.write "  {" + items.join(", ") + "},\n"
        end

        fp.write "];\n"
        fp.write "\n"
        fp.write "// Initialize table\n"
        fp.write "var table = new Tabulator(\"##{div_name}\", {\n"
        fp.write "  height: window.innerHeight-25, // Set height to window less 25 pixels for horz scrollbar\n"
        fp.write "  data: tabledata, // Assign data to table\n"
        fp.write "  columns:[\n"
        columns.each do |column|
          column_name = column.fetch(:name).gsub("\n", " ")
          sorter = column.fetch(:sorter)
          formatter = column.fetch(:formatter)
          fp.write "    {title: \"#{column_name}\", field: \"#{column_name}\", sorter: \"#{sorter}\", formatter: \"#{formatter}\""

          if column[:headerFilter] == true
            fp.write ", headerFilter: true"
          end
          if column[:headerVertical] == true
            fp.write ", headerVertical: true"
          end
          if column[:frozen] == true
            fp.write ", frozen: true"
          end

          if formatter == "link"
            formatterParams = column.fetch(:formatterParams)
            urlPrefix = formatterParams.fetch(:urlPrefix)
            fp.write ", formatterParams:{\n"
            fp.write "      labelField:\"#{column_name}\",\n"
            fp.write "      urlPrefix:\"#{urlPrefix}\"\n"
            fp.write "      }\n"
          end
          fp.write "    },\n"
        end
        fp.write "  ]\n"
        fp.write "});\n"
        fp.write "\n"

        fp.write "// Load data in chunks after table is built\n"
        fp.write "table.on(\"tableBuilt\", function() {\n"
        fp.write "    loadDataInChunks(tabledata);\n"
        fp.write "});\n"
        fp.write "\n"
        fp.rewind
        T.must(fp.read)
      end

      # Create ISA Explorer table as XLSX worksheet.
      #
      # @param table [Hash<String,Array<String>] Table data
      # @param workbook
      # @param worksheet
      sig { params(table: T::Hash[String, T::Array[T.untyped]], workbook: WriteXLSX, worksheet: Writexlsx::Worksheet).void }
      def xlsx_table(table, workbook, worksheet)
        # Add and define a header format
        header_format = workbook.add_format
        header_format.set_bold
        header_format.set_align("center")

        # Add column names in 1st row (row 0).
        col_num = 0
        table.fetch("columns").each do |column|
          worksheet.write(0, col_num, column.fetch(:name), header_format)
          col_num += 1
        end

        # Add table information in rows
        row_num = 1
        table.fetch("rows").each do |row_cells|
          col_num = 0
          row_cells.each do |cell|
            if cell.is_a?(String) || cell.is_a?(Integer)
              cell_fmt = cell.to_s
            elsif cell.is_a?(TrueClass) || cell.is_a?(FalseClass)
              cell_fmt = cell ? "Y" : "N"
            elsif cell.is_a?(Array)
              cell_fmt = cell.join(", ")
            else
              raise ArgumentError, "Unknown cell class of #{cell.class} for '#{cell}'"
            end

            worksheet.write(row_num, col_num, cell_fmt)
            col_num += 1
          end
          row_num += 1
        end

        # Set column widths to hold data width.
        worksheet.autofit
      end
    end
  end
end
